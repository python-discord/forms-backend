"""
Returns single from response by ID.
"""
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import FormResponse
from backend.route import Route


class Response(Route):
    """Get single form response by ID."""

    name = "response"
    path = "/responses/{response_id:str}"

    @requires(["authenticated", "admin"])
    async def get(self, request: Request) -> JSONResponse:
        """Returns single form response by ID."""
        if raw_response := await request.state.db.responses.find_one(
            {"_id": request.path_params["response_id"]}
        ):
            response = FormResponse(**raw_response)
            return JSONResponse(response.dict())
        else:
            return JSONResponse({"error": "not_found"}, status_code=404)
