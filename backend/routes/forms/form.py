"""
Returns single form information by ID.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route
from backend.models import Form


class SingleForm(Route):
    """
    Returns single form information by ID.

    Returns all fields for admins, otherwise only public fields.
    """

    name = "form"
    path = "/{form_id:str}"

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
