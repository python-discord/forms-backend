"""
Return a list of all publicly discoverable forms to unauthenticated users.
"""
from spectree.response import Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import constants
from backend.models import Form, FormList, Question
from backend.route import Route
from backend.validation import api

__FEATURES = [
    constants.FormFeatures.DISCOVERABLE.value,
    constants.FormFeatures.OPEN.value,
    constants.FormFeatures.REQUIRES_LOGIN.value
]

__QUESTION = Question(
    id="description",
    name="Check your cookies after pressing the button.",
    type="section",
    data={"text": "You can find cookies under \"Application\" in dev tools."},
    required=False
)

EMPTY_FORM = Form(
    id="empty_auth",
    features=__FEATURES,
    questions=[__QUESTION],
    name="Auth form",
    description="An empty form to help you get a token."
)


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

        # Return an empty form in development environments to help with authentication.
        if not forms and not constants.PRODUCTION:
            forms.append(EMPTY_FORM.dict(admin=False))

        return JSONResponse(forms)
