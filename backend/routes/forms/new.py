"""
Creates new form based on data provided.
"""
from pydantic import ValidationError
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import Form
from backend.route import Route


class FormCreate(Route):
    """
    Creates new form from JSON data.
    """

    name = "forms_create"
    path = "/new"

    @requires(["authenticated", "admin"])
    async def post(self, request: Request) -> JSONResponse:
        form_data = await request.json()
        try:
            form = Form(**form_data)
        except ValidationError as e:
            return JSONResponse(e.errors())

        await request.state.db.forms.insert_one(form.dict(by_alias=True))
        return JSONResponse(form.dict())
