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
    constants.FormFeatures.OPEN.value,
    constants.FormFeatures.REQUIRES_LOGIN.value
]
if not constants.PRODUCTION:
    __FEATURES.append(constants.FormFeatures.DISCOVERABLE.value)

__QUESTION = Question(
    id="description",
    name="Click the button below to log into the forms application.",
    type="section",
    data={"text": ""},
    required=False
)

AUTH_FORM = Form(
    id="login",
    features=__FEATURES,
    questions=[__QUESTION],
    name="Login",
    description="Log into Python Discord Forms.",
    submitted_text="This page can't be submitted."
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
        if not constants.PRODUCTION:
            forms.append(AUTH_FORM.dict(admin=False))

        return JSONResponse(forms)
