import starlette.background
from pymongo.database import Database
from spectree import Response
from starlette.authentication import requires
from starlette.responses import JSONResponse
from starlette.routing import Request

from backend import discord, route
from backend.validation import OkayResponse, api


async def refresh_roles(database: Database) -> None:
    """Connect to the discord API and refresh the roles database."""
    roles = await discord.get_role_info()
    roles_collection = database.get_collection("roles")
    roles_collection.drop()
    roles_collection.insert_many([role.dict() for role in roles])


class RolesRoute(route.Route):
    """Refreshes the roles database."""

    name = "roles"
    path = "/roles"

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=OkayResponse),
        tags=["roles"]
    )
    async def patch(self, request: Request) -> JSONResponse:
        """Refresh the roles database."""
        return JSONResponse(
            {"status": "ok"},
            background=starlette.background.BackgroundTask(refresh_roles, request.state.db)
        )
