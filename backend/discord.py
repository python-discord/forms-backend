"""Various utilities for working with the Discord API."""

import json

import httpx
import starlette.requests
from starlette import exceptions

from backend import constants
from backend.models import dtos


async def fetch_bearer_token(code: str, redirect: str, *, refresh: bool) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": constants.OAUTH2_CLIENT_ID,
            "client_secret": constants.OAUTH2_CLIENT_SECRET,
            "redirect_uri": f"{redirect}/callback",
        }

        if refresh:
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = code
        else:
            data["grant_type"] = "authorization_code"
            data["code"] = code

        r = await client.post(
            f"{constants.DISCORD_API_BASE_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=data,
        )

        r.raise_for_status()

        return r.json()


async def fetch_user_details(bearer_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/users/@me",
            headers={
                "Authorization": f"Bearer {bearer_token}",
            },
        )

        r.raise_for_status()

        return r.json()


async def _get_role_info() -> list[dtos.DiscordRole]:
    """Get information about the roles in the configured guild."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}/roles",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"},
        )

        r.raise_for_status()
        return [dtos.DiscordRole(**role) for role in r.json()]


async def get_roles(
    *,
    force_refresh: bool = False,
) -> list[dtos.DiscordRole]:
    """
    Get a list of all roles from the cache, or discord API if not available.

    If `force_refresh` is True, the cache is skipped and the roles are updated.
    """
    role_cache_key = "forms-backend:role_cache"
    if not force_refresh:
        roles = await constants.REDIS_CLIENT.hgetall(role_cache_key)
        if roles:
            return [
                dtos.DiscordRole(**json.loads(role_data)) for role_id, role_data in roles.items()
            ]

    roles = await _get_role_info()
    await constants.REDIS_CLIENT.hmset(role_cache_key, {role.id: role.json() for role in roles})
    await constants.REDIS_CLIENT.expire(role_cache_key, 60 * 60 * 24)  # 1 day
    return roles


async def _fetch_member_api(member_id: str) -> dtos.DiscordMember | None:
    """Get a member by ID from the configured guild using the discord API."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}"
            f"/members/{member_id}",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"},
        )

        if r.status_code == 404:
            return None

        r.raise_for_status()
        return dtos.DiscordMember(**r.json())


async def get_member(
    user_id: str,
    *,
    force_refresh: bool = False,
) -> dtos.DiscordMember | None:
    """
    Get a member from the cache, or from the discord API.

    If `force_refresh` is True, the cache is skipped and the entry is updated.
    None may be returned if the member object does not exist.
    """
    member_key = f"forms-backend:member_cache:{user_id}"

    if not force_refresh:
        result = await constants.REDIS_CLIENT.get(member_key)
        if result:
            return dtos.DiscordMember(**json.loads(result))

    member = await _fetch_member_api(user_id)
    if member:
        await constants.REDIS_CLIENT.set(member_key, member.json(), ex=60 * 60)

    return member


class FormNotFoundError(exceptions.HTTPException):
    """The requested form was not found."""


class UnauthorizedError(exceptions.HTTPException):
    """You are not authorized to use this resource."""


async def _verify_access_helper(
    form_id: str,
    request: starlette.requests.Request,
    attribute: str,
) -> None:
    """A low level helper to validate access to a form resource based on the user's scopes."""
    form = await request.state.db.forms.find_one({"_id": form_id})

    if not form:
        raise FormNotFoundError(status_code=404)

    # Short circuit all resources for forms admins
    if "admin" in request.auth.scopes:
        return

    form = dtos.Form(**form)

    for role_id in getattr(form, attribute, None) or []:
        role = await request.state.db.roles.find_one({"id": role_id})
        if not role:
            continue

        role = dtos.DiscordRole(**json.loads(role["data"]))

        if role.name in request.auth.scopes:
            return

    raise UnauthorizedError(status_code=401)


async def verify_response_access(form_id: str, request: starlette.requests.Request) -> None:
    """Ensure the user can access responses on the requested resource."""
    await _verify_access_helper(form_id, request, "response_readers")


async def verify_edit_access(form_id: str, request: starlette.requests.Request) -> None:
    """Ensure the user can view and modify the requested resource."""
    await _verify_access_helper(form_id, request, "editors")
