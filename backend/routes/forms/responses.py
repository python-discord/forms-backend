"""
Returns all form responses by form ID.
"""
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import FormResponse
from backend.route import Route


class Responses(Route):
    """
    Returns all form responses by form ID.
    """

    name = "form_responses"
    path = "/{form_id:str}/responses"

    @requires(["authenticated", "admin"])
    async def get(self, request: Request) -> JSONResponse:
        """Returns all form responses by form ID."""
        cursor = request.state.db.responses.find(
            {"form_id": request.path_params["form_id"]}
        )
        if raw_responses := await cursor.to_list(None):
            responses = [FormResponse(**response) for response in raw_responses]
            return JSONResponse([response.dict() for response in responses])
        else:
            return JSONResponse({"error": "not_found"}, 404)
