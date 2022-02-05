"""Various utilities for working with the Discord API."""

import datetime
import json
import typing

import httpx
import starlette.requests
from pymongo.database import Database

from backend import constants, models


async def fetch_bearer_token(code: str, redirect: str, *, refresh: bool) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": constants.OAUTH2_CLIENT_ID,
            "client_secret": constants.OAUTH2_CLIENT_SECRET,
            "redirect_uri": f"{redirect}/callback"
        }

        if refresh:
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = code
        else:
            data["grant_type"] = "authorization_code"
            data["code"] = code

        r = await client.post(f"{constants.DISCORD_API_BASE_URL}/oauth2/token", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)

        r.raise_for_status()

        return r.json()


async def fetch_user_details(bearer_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{constants.DISCORD_API_BASE_URL}/users/@me", headers={
            "Authorization": f"Bearer {bearer_token}"
        })

        r.raise_for_status()

        return r.json()


async def _get_role_info() -> list[models.DiscordRole]:
    """Get information about the roles in the configured guild."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}/roles",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"}
        )

        r.raise_for_status()
        return [models.DiscordRole(**role) for role in r.json()]


async def get_roles(
    database: Database, *, force_refresh: bool = False
) -> list[models.DiscordRole]:
    """
    Get a list of all roles from the cache, or discord API if not available.

    If `force_refresh` is True, the cache is skipped and the roles are updated.
    """
    collection = database.get_collection("roles")

    if force_refresh:
        # Drop all values in the collection
        await collection.delete_many({})

    # `create_index` creates the index if it does not exist, or passes
    # This handles TTL on role objects
    await collection.create_index(
        "inserted_at",
        expireAfterSeconds=60 * 60 * 24,  # 1 day
        name="inserted_at",
    )

    roles = [models.DiscordRole(**json.loads(role["data"])) async for role in collection.find()]

    if len(roles) == 0:
        # Fetch roles from the API and insert into the database
        roles = await _get_role_info()
        await collection.insert_many({
            "name": role.name,
            "id": role.id,
            "data": role.json(),
            "inserted_at": datetime.datetime.now(tz=datetime.timezone.utc),
        } for role in roles)

    return roles


async def _fetch_member_api(member_id: str) -> typing.Optional[models.DiscordMember]:
    """Get a member by ID from the configured guild using the discord API."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}"
            f"/members/{member_id}",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"}
        )

        if r.status_code == 404:
            return None

        r.raise_for_status()
        return models.DiscordMember(**r.json())


async def get_member(
    database: Database, user_id: str, *, force_refresh: bool = False
) -> typing.Optional[models.DiscordMember]:
    """
    Get a member from the cache, or from the discord API.

    If `force_refresh` is True, the cache is skipped and the entry is updated.
    None may be returned if the member object does not exist.
    """
    collection = database.get_collection("discord_members")

    if force_refresh:
        await collection.delete_one({"user": user_id})

    # `create_index` creates the index if it does not exist, or passes
    # This handles TTL on member objects
    await collection.create_index(
        "inserted_at",
        expireAfterSeconds=60 * 60,  # 1 hour
        name="inserted_at",
    )

    result = await collection.find_one({"user": user_id})

    if result is not None:
        return models.DiscordMember(**json.loads(result["data"]))

    member = await _fetch_member_api(user_id)

    if not member:
        return None

    await collection.insert_one({
        "user": user_id,
        "data": member.json(),
        "inserted_at": datetime.datetime.now(tz=datetime.timezone.utc),
    })
    return member


class FormNotFoundError(Exception):
    """The requested form was not found."""


async def _verify_access_helper(
    form_id: str, request: starlette.requests.Request, attribute: str
) -> bool:
    """A low level helper to validate access to a form resource based on the user's scopes."""
    # Short circuit all resources for admins
    if "admin" in request.auth.scopes:
        return True

    form = await request.state.db.forms.find_one({"id": form_id})

    if not form:
        raise FormNotFoundError()

    form = models.Form(**form)

    for role_id in getattr(form, attribute) or []:
        role = await request.state.db.roles.find_one({"id": role_id})
        if not role:
            continue

        role = models.DiscordRole(**json.loads(role["data"]))

        if role.name in request.auth.scopes:
            return True

    return False


async def verify_response_access(form_id: str, request: starlette.requests.Request) -> bool:
    """Ensure the user can access responses on the requested resource."""
    return await _verify_access_helper(form_id, request, "response_readers")


async def verify_edit_access(form_id: str, request: starlette.requests.Request) -> bool:
    """Ensure the user can view and modify the requested resource."""
    return await _verify_access_helper(form_id, request, "editors")
