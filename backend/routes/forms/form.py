"""Returns, updates or deletes a single form given an ID."""

import json.decoder

import deepmerge
from pydantic import ValidationError
from spectree.response import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import constants, discord
from backend.models import Form
from backend.route import Route
from backend.routes.forms.discover import AUTH_FORM
from backend.validation import ErrorMessage, OkayResponse, api

PUBLIC_FORM_FEATURES = (constants.FormFeatures.OPEN, constants.FormFeatures.DISCOVERABLE)


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
        form_id = request.path_params["form_id"].lower()

        if form_id == AUTH_FORM.id:
            # Empty form for login purposes
            return JSONResponse(AUTH_FORM.dict(admin=False))

        try:
            await discord.verify_edit_access(form_id, request)
            admin = True
        except discord.FormNotFoundError:
            return JSONResponse({"error": "not_found"}, status_code=404)
        except discord.UnauthorizedError:
            admin = False

        filters = {
            "_id": form_id,
        }

        if not admin:
            filters["features"] = {"$in": ["OPEN", "DISCOVERABLE"]}

        form = await request.state.db.forms.find_one(filters)
        if not form:
            return JSONResponse({"error": "not_found"}, status_code=404)

        return JSONResponse(Form(**form).dict(admin=admin))

    @requires(["authenticated"])
    @api.validate(
        resp=Response(
            HTTP_200=OkayResponse,
            HTTP_400=ErrorMessage,
            HTTP_404=ErrorMessage,
        ),
        tags=["forms"],
    )
    async def patch(self, request: Request) -> JSONResponse:
        """Updates form by ID."""
        try:
            data = await request.json()
        except json.decoder.JSONDecodeError:
            return JSONResponse({"error": "Expected a JSON body."}, 400)

        form_id = request.path_params["form_id"].lower()
        await discord.verify_edit_access(form_id, request)

        if raw_form := await request.state.db.forms.find_one({"_id": form_id}):
            if "_id" in data or "id" in data:
                if (data.get("id") or data.get("_id")) != form_id:
                    return JSONResponse({"error": "locked_field"}, status_code=400)

            # Build Data Merger
            merge_strategy = [
                (dict, ["merge"]),
            ]
            merger = deepmerge.Merger(merge_strategy, ["override"], ["override"])

            # Merge Form Data
            updated_form = merger.merge(raw_form, data)

            try:
                form = Form(**updated_form)
            except ValidationError as e:
                return JSONResponse(e.errors(), status_code=422)

            await request.state.db.forms.replace_one({"_id": form_id}, form.dict())

            return JSONResponse(form.dict())
        return JSONResponse({"error": "not_found"}, status_code=404)

    @requires(["authenticated", "admin"])
    @api.validate(
        resp=Response(HTTP_200=OkayResponse, HTTP_401=ErrorMessage, HTTP_404=ErrorMessage),
        tags=["forms"],
    )
    async def delete(self, request: Request) -> JSONResponse:
        """Deletes form by ID."""
        form_id = request.path_params["form_id"].lower()
        await discord.verify_edit_access(form_id, request)

        await request.state.db.forms.delete_one({"_id": form_id})
        await request.state.db.responses.delete_many({"form_id": form_id})

        return JSONResponse({"status": "ok"})
