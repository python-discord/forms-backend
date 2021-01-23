"""
Return a list of all publicly discoverable forms to unauthenticated users.
"""
from spectree.response import Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.models import Form, FormList
from backend.route import Route
from backend.validation import api


class DiscoverableFormsList(Route):
    """
    List all discoverable forms that should be shown on the homepage.
    """

    name = "discoverable_forms_list"
    path = "/discoverable"

    @api.validate(resp=Response(HTTP_200=FormList), tags=["forms"])
    async def get(self, request: Request) -> JSONResponse:
        """List all discoverable forms that should be shown on the homepage."""
        forms = []
        cursor = request.state.db.forms.find({"features": "DISCOVERABLE"}).sort("name")

        # Parse it to Form and then back to dictionary
        # to replace _id with id
        for form in await cursor.to_list(None):
            forms.append(Form(**form))

        forms = [form.dict(admin=False) for form in forms]

        return JSONResponse(
            forms
        )
