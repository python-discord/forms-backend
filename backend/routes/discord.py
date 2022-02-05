"""Routes which directly interact with discord related data."""

import pydantic
from spectree import Response
from starlette.authentication import requires
from starlette.responses import JSONResponse
from starlette.routing import Request

from backend import discord, models, route
from backend.validation import ErrorMessage, OkayResponse, api

NOT_FOUND_EXCEPTION = JSONResponse(
    {"error": "Could not find the requested resource in the guild or cache."}, status_code=404
)


class RolesRoute(route.Route):
    """Refreshes the roles database."""

    name = "roles"
    path = "/roles"

    class RolesResponse(pydantic.BaseModel):
        """A list of all roles on the configured server."""

        roles: list[models.DiscordRole]

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=OkayResponse),
        tags=["roles"]
    )
    async def patch(self, request: Request) -> JSONResponse:
        """Refresh the roles database."""
        roles = await discord.get_roles(request.state.db, force_refresh=True)

        return JSONResponse(
            {"status": "ok"},
        )


class MemberRoute(route.Route):
    """Retrieve information about a server member."""

    name = "member"
    path = "/member"

    class MemberRequest(pydantic.BaseModel):
        """An ID of the member to update."""

        user_id: str

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=models.DiscordMember, HTTP_400=ErrorMessage),
        json=MemberRequest,
        tags=["auth"]
    )
    async def delete(self, request: Request):
        """Force a resync of the cache for the given user."""
        body = await request.json()
        member = await discord.get_member(request.state.db, body["user_id"], force_refresh=True)

        if member:
            return JSONResponse(member.dict())
        else:
            return NOT_FOUND_EXCEPTION

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=models.DiscordMember, HTTP_400=ErrorMessage),
        json=MemberRequest,
        tags=["auth"]
    )
    async def get(self, request: Request):
        """Get a user's roles on the configured server."""
        body = await request.json()
        member = await discord.get_member(request.state.db, body["user_id"])

        if member:
            return JSONResponse(member.dict())
        else:
            return NOT_FOUND_EXCEPTION
