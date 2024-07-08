"""Return a list of all forms to authenticated users."""

from spectree.response import Response
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.constants import WebHook
from backend.models import Form, FormList
from backend.models.form import validate_hook_url
from backend.route import Route
from backend.validation import ErrorMessage, OkayResponse, api


class FormsList(Route):
    """List all available forms for authorized viewers."""

    name = "forms_list_create"
    path = "/"

    @requires(["authenticated", "Admins"])
    @api.validate(resp=Response(HTTP_200=FormList), tags=["forms"])
    async def get(self, request: Request) -> JSONResponse:
        """Return a list of all forms to authenticated users."""
        cursor = request.state.db.forms.find()

        forms = [Form(**form).dict() for form in await cursor.to_list(None)]

        return JSONResponse(forms)

    @requires(["authenticated", "Helpers"])
    @api.validate(
        json=Form,
        resp=Response(HTTP_200=OkayResponse, HTTP_400=ErrorMessage),
        tags=["forms"],
    )
    async def post(self, request: Request) -> JSONResponse:
        """Create a new form."""
        form_data = await request.json()

        # Verify Webhook
        try:
            # Get url from request
            webhook = form_data[WebHook.__name__.lower()]
            if webhook is not None:
                url = webhook[WebHook.URL.value]

                # Validate URL
                validation = await validate_hook_url(url)
                if validation:
                    return JSONResponse(validation.errors(), status_code=422)

        except KeyError:
            pass

        form = Form(**form_data)

        if await request.state.db.forms.find_one({"_id": form.id}):
            return JSONResponse({"error": "id_taken"}, status_code=400)

        await request.state.db.forms.insert_one(form.dict(by_alias=True))
        return JSONResponse(form.dict())
