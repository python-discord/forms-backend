"""
Submit a form.
"""

import binascii
import hashlib
from typing import Any, Optional
import uuid

import httpx
from pydantic.main import BaseModel
from pydantic import ValidationError
from spectree import Response
from starlette.requests import Request

from starlette.responses import JSONResponse

from backend.constants import HCAPTCHA_API_SECRET, FormFeatures
from backend.models import Form, FormResponse
from backend.route import Route
from backend.validation import AuthorizationHeaders, ErrorMessage, api

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
HCAPTCHA_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}


class SubmissionResponse(BaseModel):
    form: Form
    response: FormResponse


class PartialSubmission(BaseModel):
    response: dict[str, Any]
    captcha: Optional[str]


class SubmitForm(Route):
    """
    Submit a form with the provided form ID.
    """

    name = "submit_form"
    path = "/submit/{form_id:str}"

    @api.validate(
        json=PartialSubmission,
        resp=Response(
            HTTP_200=SubmissionResponse,
            HTTP_404=ErrorMessage,
            HTTP_400=ErrorMessage
        ),
        headers=AuthorizationHeaders,
        tags=["forms", "responses"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Submit a response to the form."""
        data = await request.json()

        data["timestamp"] = None

        if form := await request.state.db.forms.find_one(
            {"_id": request.path_params["form_id"], "features": "OPEN"}
        ):
            form = Form(**form)
            response = data.copy()
            response["id"] = str(uuid.uuid4())
            response["form_id"] = form.id

            if FormFeatures.DISABLE_ANTISPAM.value not in form.features:
                ip_hash_ctx = hashlib.md5()
                ip_hash_ctx.update(request.client.host.encode())
                ip_hash = binascii.hexlify(ip_hash_ctx.digest())
                user_agent_hash_ctx = hashlib.md5()
                user_agent_hash_ctx.update(request.headers["User-Agent"].encode())
                user_agent_hash = binascii.hexlify(user_agent_hash_ctx.digest())

                async with httpx.AsyncClient() as client:
                    query_params = {
                        "secret": HCAPTCHA_API_SECRET,
                        "response": data.get("captcha")
                    }
                    r = await client.post(
                        HCAPTCHA_VERIFY_URL,
                        params=query_params,
                        headers=HCAPTCHA_HEADERS
                    )
                    r.raise_for_status()
                    captcha_data = r.json()

                response["antispam"] = {
                    "ip_hash": ip_hash.decode(),
                    "user_agent_hash": user_agent_hash.decode(),
                    "captcha_pass": captcha_data["success"]
                }

            if FormFeatures.REQUIRES_LOGIN.value in form.features:
                if request.user.is_authenticated:
                    response["user"] = request.user.payload

                    if FormFeatures.COLLECT_EMAIL.value in form.features and "email" not in response["user"]:  # noqa
                        return JSONResponse({
                            "error": "email_required"
                        }, status_code=400)
                else:
                    return JSONResponse({
                        "error": "missing_discord_data"
                    }, status_code=400)

            missing_fields = []
            for question in form.questions:
                if question.id not in response["response"]:
                    missing_fields.append(question.id)

            if missing_fields:
                return JSONResponse({
                    "error": "missing_fields",
                    "fields": missing_fields
                }, status_code=400)

            try:
                response_obj = FormResponse(**response)
            except ValidationError as e:
                return JSONResponse(e.errors())

            await request.state.db.responses.insert_one(
                response_obj.dict(by_alias=True)
            )

            return JSONResponse({
                "form": form.dict(),
                "response": response_obj.dict()
            })
        else:
            return JSONResponse({
                "error": "Open form not found"
            })
