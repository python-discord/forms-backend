"""
Returns all form responses by form ID.
"""
from spectree import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import FormResponse, ResponseList
from backend.route import Route
from backend.validation import api, ErrorMessage


class Responses(Route):
    """
    Returns all form responses by form ID.
    """

    name = "form_responses"
    path = "/{form_id:str}/responses"

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=ResponseList, HTTP_404=ErrorMessage),
        tags=["forms", "responses"]
    )
    async def get(self, request: Request) -> JSONResponse:
        """Returns all form responses by form ID."""
        if not await request.state.db.forms.find_one(
            {"_id": request.path_params["form_id"]}
        ):
            return JSONResponse({"error": "not_found"}, 404)

        cursor = request.state.db.responses.find(
            {"form_id": request.path_params["form_id"]}
        )
        responses = [
            FormResponse(**response) for response in await cursor.to_list(None)
        ]
        return JSONResponse([response.dict() for response in responses])
