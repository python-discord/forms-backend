"""Returns or deletes form response by ID."""

from spectree import Response as RouteResponse
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import discord
from backend.models import FormResponse
from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api


class Response(Route):
    """Get or delete single form response by ID."""

    name = "response"
    path = "/{form_id:str}/responses/{response_id:str}"

    @requires(["authenticated"])
    @api.validate(
        resp=RouteResponse(HTTP_200=FormResponse, HTTP_404=ErrorMessage),
        tags=["forms", "responses"],
    )
    async def get(self, request: Request) -> JSONResponse:
        """Return a single form response by ID."""
        form_id = request.path_params["form_id"]
        await discord.verify_response_access(form_id, request)

        if raw_response := await request.state.db.responses.find_one(
            {
                "_id": request.path_params["response_id"],
                "form_id": form_id,
            },
        ):
            response = FormResponse(**raw_response)
            return JSONResponse(response.dict())
        return JSONResponse({"error": "response_not_found"}, status_code=404)

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=RouteResponse(HTTP_200=OkayResponse, HTTP_404=ErrorMessage),
        tags=["forms", "responses"],
    )
    async def delete(self, request: Request) -> JSONResponse:
        """Delete a form response by ID."""
        if not await request.state.db.responses.find_one(
            {
                "_id": request.path_params["response_id"],
                "form_id": request.path_params["form_id"],
            },
        ):
            return JSONResponse({"error": "not_found"}, status_code=404)

        await request.state.db.responses.delete_one(
            {"_id": request.path_params["response_id"]},
        )
        return JSONResponse({"status": "ok"})
