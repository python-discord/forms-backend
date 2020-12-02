"""
Return a list of all forms to authenticated users.
"""
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.models import Form


class FormsList(Route):
    """
    List all available forms for administrator viewing.
    """

    name = "forms_list"
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
