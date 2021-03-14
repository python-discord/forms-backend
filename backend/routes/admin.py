"""
Adds new admin user.
"""
import logging

from pydantic import BaseModel, Field
from spectree import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api

logger = logging.getLogger(__name__)


class AdminModel(BaseModel):
    id: str = Field(alias="_id")


class AdminRoute(Route):
    """Adds new admin user."""

    name = "admin"
    path = "/admin"

    @requires(["authenticated", "admin"])
    @api.validate(
        json=AdminModel,
        resp=Response(HTTP_200=OkayResponse, HTTP_400=ErrorMessage),
        tags=["admin"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Grant a user administrator privileges."""
        data = await request.json()
        admin = AdminModel(**data)

        logger.info(f"Trying to add a new admin with ID: {admin.id}")

        if await request.state.db.admins.find_one(
            {"_id": admin.id}
        ):
            return JSONResponse({"error": "already_exists"}, status_code=400)

        await request.state.db.admins.insert_one(admin.dict(by_alias=True))
        return JSONResponse({"status": "ok"})
