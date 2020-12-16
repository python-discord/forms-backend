"""
Use a token received from the Discord OAuth2 system to fetch user information.
"""

import httpx
import jwt
from pydantic.fields import Field
from pydantic.main import BaseModel
from spectree.response import Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.constants import SECRET_KEY
from backend.route import Route
from backend.discord import fetch_bearer_token, fetch_user_details
from backend.validation import ErrorMessage, api


class AuthorizeRequest(BaseModel):
    token: str = Field(description="The access token received from Discord.")


class AuthorizeResponse(BaseModel):
    token: str = Field(description="A JWT token containing the user information")


class AuthorizeRoute(Route):
    """
    Use the authorization code from Discord to generate a JWT token.
    """

    name = "authorize"
    path = "/authorize"

    @api.validate(
        json=AuthorizeRequest,
        resp=Response(HTTP_200=AuthorizeResponse, HTTP_400=ErrorMessage),
        tags=["auth"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Generate an authorization token."""
        data = await request.json()

        try:
            bearer_token = await fetch_bearer_token(data["token"])
            user_details = await fetch_user_details(bearer_token["access_token"])
        except httpx.HTTPStatusError:
            return JSONResponse({
                "error": "auth_failure"
            }, status_code=400)

        user_details["admin"] = await request.state.db.admins.find_one(
            {"_id": user_details["id"]}
        ) is not None

        token = jwt.encode(user_details, SECRET_KEY, algorithm="HS256")

        return JSONResponse({
            "token": token.decode()
        })
