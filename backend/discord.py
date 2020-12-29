"""Various utilities for working with the Discord API."""
import httpx

from backend.constants import (
    DISCORD_API_BASE_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, OAUTH2_REDIRECT_URI
)


async def fetch_bearer_token(access_code: str) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": access_code,
            "redirect_uri": OAUTH2_REDIRECT_URI
        }

        r = await client.post(f"{DISCORD_API_BASE_URL}/oauth2/token", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)

        r.raise_for_status()

        return r.json()


async def fetch_user_details(bearer_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{DISCORD_API_BASE_URL}/users/@me", headers={
            "Authorization": f"Bearer {bearer_token}"
        })

        r.raise_for_status()

        return r.json()
