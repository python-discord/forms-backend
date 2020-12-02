"""
Return a list of all forms to authenticated users.
"""
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route


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
            forms.append(form)

        return JSONResponse(
            forms
        )
