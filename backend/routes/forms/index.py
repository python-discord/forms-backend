"""
Return a list of all forms to authenticated users.
"""
from pydantic import ValidationError
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.models import Form


class FormsList(Route):
    """
    List all available forms for administrator viewing.
    """

    name = "forms_list_create"
    path = "/"

    @requires(["authenticated", "admin"])
    async def get(self, request: Request) -> JSONResponse:
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
    async def post(self, request: Request) -> JSONResponse:
        form_data = await request.json()
        try:
            form = Form(**form_data)
        except ValidationError as e:
            return JSONResponse(e.errors())

        if await request.state.db.forms.find_one({"_id": form.id}):
            return JSONResponse({
                "error": "Form with same ID already exists."
            }, status_code=400)

        await request.state.db.forms.insert_one(form.dict(by_alias=True))
        return JSONResponse(form.dict())
