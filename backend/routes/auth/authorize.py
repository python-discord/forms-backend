"""
Use a token received from the Discord OAuth2 system to fetch user information.
"""

import jwt
from starlette.responses import JSONResponse

from backend.constants import SECRET_KEY
from backend.route import Route
from backend.discord import fetch_bearer_token, fetch_user_details


class AuthorizeRoute(Route):
    """
    Use the authorization code from Discord to generate a JWT token.
    """

    name = "authorize"
    path = "/authorize"

    async def post(self, request):
        data = await request.json()

        bearer_token = await fetch_bearer_token(data["token"])
        user_details = await fetch_user_details(bearer_token["access_token"])

        token = jwt.encode(user_details, SECRET_KEY, algorithm="HS256")

        return JSONResponse({
            "token": token.decode()
        })
