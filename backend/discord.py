"""Various utilities for working with the Discord API."""
import httpx

from backend.constants import (
    OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, OAUTH2_REDIRECT_URI
)

API_BASE_URL = "https://discord.com/api/v8"


async def fetch_bearer_token(code: str, *, refresh: bool) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET,
            "redirect_uri": OAUTH2_REDIRECT_URI
        }

        if refresh:
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = code
        else:
            data["grant_type"] = "authorization_code"
            data["code"] = code

        r = await client.post(f"{API_BASE_URL}/oauth2/token", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)

        r.raise_for_status()

        return r.json()


async def fetch_user_details(bearer_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE_URL}/users/@me", headers={
            "Authorization": f"Bearer {bearer_token}"
        })

        r.raise_for_status()

        return r.json()
