"""
Returns, updates or deletes a single form given an ID.
"""
import deepmerge
from pydantic import ValidationError
from spectree.response import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import Form
from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api


class SingleForm(Route):
    """
    Returns, updates or deletes a single form given an ID.

    Returns all fields for admins, otherwise only public fields.
    """

    name = "form"
    path = "/{form_id:str}"

    @api.validate(resp=Response(HTTP_200=Form, HTTP_404=ErrorMessage), tags=["forms"])
    async def get(self, request: Request) -> JSONResponse:
        """Returns single form information by ID."""
        admin = request.user.payload["admin"] if request.user.is_authenticated else False  # noqa

        filters = {
            "_id": request.path_params["form_id"]
        }

        if not admin:
            filters["features"] = "OPEN"

        if raw_form := await request.state.db.forms.find_one(filters):
            form = Form(**raw_form)
            return JSONResponse(form.dict(admin=admin))

        return JSONResponse({"error": "not_found"}, status_code=404)

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(
            HTTP_200=OkayResponse,
            HTTP_400=ErrorMessage,
            HTTP_404=ErrorMessage
        ),
        tags=["forms"]
    )
    async def patch(self, request: Request) -> JSONResponse:
        """Updates form by ID."""
        data = await request.json()

        form_id = {"_id": request.path_params["form_id"]}
        if raw_form := await request.state.db.forms.find_one(form_id):
            if "_id" in data or "id" in data:
                return JSONResponse({"error": "locked_field"}, status_code=400)

            # Build Data Merger
            merge_strategy = [
                (dict, ["merge"])
            ]
            merger = deepmerge.Merger(merge_strategy, ["override"], ["override"])

            # Merge Form Data
            updated_form = merger.merge(raw_form, data)

            try:
                form = Form(**updated_form)
            except ValidationError as e:
                return JSONResponse(e.errors(), status_code=422)

            await request.state.db.forms.replace_one(
                {"_id": request.path_params["form_id"]},
                form.dict()
            )

            return JSONResponse(form.dict())
        else:
            return JSONResponse({"error": "not_found"}, status_code=404)

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=OkayResponse, HTTP_404=ErrorMessage),
        tags=["forms"]
    )
    async def delete(self, request: Request) -> JSONResponse:
        """Deletes form by ID."""
        if not await request.state.db.forms.find_one(
            {"_id": request.path_params["form_id"]}
        ):
            return JSONResponse({"error": "not_found"}, status_code=404)

        await request.state.db.forms.delete_one(
            {"_id": request.path_params["form_id"]}
        )
        await request.state.db.responses.delete_many(
            {"form_id": request.path_params["form_id"]}
        )

        return JSONResponse({"status": "ok"})
