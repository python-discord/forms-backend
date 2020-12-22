"""
Adds new admin user.
"""
from spectree import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api


class AdminRoute(Route):
    """Adds new admin user."""

    name = "admin"
    path = "/admin"

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=OkayResponse, HTTP_400=ErrorMessage),
        tags=["admin"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Inserts new administrator user to DB."""
        data = await request.json()
        if "id" not in data:
            return JSONResponse({"error": "missing_id"}, status_code=400)

        await request.state.db.admins.insert_one({"_id": str(data["id"])})
        return JSONResponse({"status": "ok"})
