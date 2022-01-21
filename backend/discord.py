"""Various utilities for working with the Discord API."""
import httpx

from backend import constants
from backend.models import discord_role, discord_user


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


async def get_role_info() -> list[discord_role.DiscordRole]:
    """Get information about the roles in the configured guild."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}/roles",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"}
        )

        r.raise_for_status()
        return [discord_role.DiscordRole(**role) for role in r.json()]


async def get_member(member_id: str) -> discord_user.DiscordMember:
    """Get a member by ID from the configured guild."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}"
            f"/members/{member_id}",
            headers={"Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"}
        )

        r.raise_for_status()
        return discord_user.DiscordMember(**r.json())
