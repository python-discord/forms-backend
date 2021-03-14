"""
Returns all form responses by form ID.
"""
import logging

from pydantic import BaseModel
from spectree import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import FormResponse, ResponseList
from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api

logger = logging.getLogger(__name__)


class ResponseIdList(BaseModel):
    ids: list[str]


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

    @requires(["authenticated", "admin"])
    @api.validate(
        json=ResponseIdList,
        resp=Response(
            HTTP_200=OkayResponse,
            HTTP_404=ErrorMessage,
            HTTP_400=ErrorMessage
        ),
        tags=["forms", "responses"]
    )
    async def delete(self, request: Request) -> JSONResponse:
        """Bulk deletes form responses by IDs."""
        form_id = {"_id": request.path_params["form_id"]}
        logger.info(f"Bulk deleting responses for form with ID: {form_id.get('_id')}")

        if not await request.state.db.forms.find_one(form_id):
            return JSONResponse({"error": "not_found"}, status_code=404)

        data = await request.json()
        response_ids = ResponseIdList(**data)

        # Convert IDs to set to remove duplicates
        ids = set(response_ids.ids)

        cursor = request.state.db.responses.find(
            {"_id": {"$in": list(ids)}}  # Convert here back to list, may throw error.
        )
        entries = [
            FormResponse(**submission) for submission in await cursor.to_list(None)
        ]
        actual_ids = {entry.id for entry in entries}

        if len(ids) != len(actual_ids):
            return JSONResponse(
                {
                    "error": "responses_not_found",
                    "ids": list(ids - actual_ids)
                },
                status_code=404
            )

        if any(entry.form_id != request.path_params["form_id"] for entry in entries):
            return JSONResponse(
                {
                    "error": "wrong_form",
                    "ids": list(
                        entry.id for entry in entries
                        if entry.id != request.path_params["form_id"]
                    )
                },
                status_code=400
            )

        logger.debug(f"Executing deletion for the following responses: {','.join(actual_ids)}")
        await request.state.db.responses.delete_many(
            {
                "_id": {"$in": list(actual_ids)}
            }
        )
        return JSONResponse({"status": "ok"})
