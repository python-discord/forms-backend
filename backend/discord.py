"""Various utilities for working with the Discord API."""
import asyncio
import typing
from urllib import parse

import httpx
from starlette.requests import Request

from backend import constants
from backend.authentication.user import User
from backend.models import Form, FormResponse

API_BASE_URL = "https://discord.com/api/v8/"
DISCORD_HEADERS = {
    "Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"
}


async def make_request(
        method: str,
        url: str,
        json: dict[str, any] = None,
        headers: dict[str, str] = None
) -> httpx.Response:
    """Make a request to the discord API."""
    url = parse.urljoin(API_BASE_URL, url)
    _headers = DISCORD_HEADERS.copy()
    _headers.update(headers if headers else {})

    async with httpx.AsyncClient() as client:
        if json is not None:
            request = client.request(method, url, json=json, headers=_headers)
        else:
            request = client.request(method, url, headers=_headers)
        resp = await request

        # Handle Rate Limits
        while resp.status_code == 429:
            retry_after = float(resp.headers["X-Ratelimit-Reset-After"])
            await asyncio.sleep(retry_after)
            resp = await request

        resp.raise_for_status()
        return resp


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

        r = await client.post(f"{API_BASE_URL}/oauth2/token", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)

        r.raise_for_status()

        return r.json()


async def fetch_user_details(bearer_token: str) -> dict:
    r = await make_request("GET", "users/@me", headers={"Authorization": f"Bearer {bearer_token}"})
    r.raise_for_status()
    return r.json()
