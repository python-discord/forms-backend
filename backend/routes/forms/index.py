"""
Return a list of all forms to authenticated users.
"""
from spectree.response import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.models import Form, FormList
from backend.validation import ErrorMessage, OkayResponse, api


class FormsList(Route):
    """
    List all available forms for administrator viewing.
    """

    name = "forms_list_create"
    path = "/"

    @requires(["authenticated", "admin"])
    @api.validate(resp=Response(HTTP_200=FormList), tags=["forms"])
    async def get(self, request: Request) -> JSONResponse:
        """Return a list of all forms to authenticated users."""
        forms = []
        cursor = request.state.db.forms.find()

        for form in await cursor.to_list(None):
            forms.append(Form(**form))  # For converting _id to id

        # Covert them back to dictionaries
        forms = [form.dict() for form in forms]

        return JSONResponse(
            forms
        )

    @requires(["authenticated", "admin"])
    @api.validate(
        json=Form,
        resp=Response(HTTP_200=OkayResponse, HTTP_400=ErrorMessage),
        tags=["forms"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Create a new form."""
        form_data = await request.json()

        form = Form(**form_data)

        if await request.state.db.forms.find_one({"_id": form.id}):
            return JSONResponse({
                "error": "id_taken"
            }, status_code=400)

        await request.state.db.forms.insert_one(form.dict(by_alias=True))
        return JSONResponse(form.dict())
