"""
Submit a form.
"""

import asyncio
import binascii
import datetime
import hashlib
import uuid
from typing import Any, Optional

import httpx
from pydantic import ValidationError
from pydantic.main import BaseModel
from spectree import Response
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import constants
from backend.authentication.user import User
from backend.models import Form, FormResponse
from backend.route import Route
from backend.routes.auth.authorize import set_response_token
from backend.routes.forms.unittesting import execute_unittest
from backend.validation import ErrorMessage, api

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
HCAPTCHA_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}

DISCORD_HEADERS = {
    "Authorization": f"Bot {constants.DISCORD_BOT_TOKEN}"
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
        tags=["forms", "responses"]
    )
    async def post(self, request: Request) -> JSONResponse:
        """Submit a response to the form."""
        response = await self.submit(request)

        # Silently try to update user data
        try:
            if hasattr(request.user, User.refresh_data.__name__):
                old = request.user.token
                await request.user.refresh_data()

                if old != request.user.token:
                    try:
                        expiry = datetime.datetime.fromisoformat(
                            request.user.decoded_token.get("expiry")
                        )
                    except ValueError:
                        expiry = None

                    expiry_seconds = (expiry - datetime.datetime.now()).seconds
                    await set_response_token(response, request, request.user.token, expiry_seconds)

        except httpx.HTTPStatusError:
            pass

        return response

    async def submit(self, request: Request) -> JSONResponse:
        """Helper method for handling submission logic."""
        data = await request.json()
        data["timestamp"] = None

        if form := await request.state.db.forms.find_one(
            {"_id": request.path_params["form_id"], "features": "OPEN"}
        ):
            form = Form(**form)
            response = data.copy()
            response["id"] = str(uuid.uuid4())
            response["form_id"] = form.id

            if constants.FormFeatures.DISABLE_ANTISPAM.value not in form.features:
                ip_hash_ctx = hashlib.md5()
                ip_hash_ctx.update(request.client.host.encode())
                ip_hash = binascii.hexlify(ip_hash_ctx.digest())
                user_agent_hash_ctx = hashlib.md5()
                user_agent_hash_ctx.update(request.headers["User-Agent"].encode())
                user_agent_hash = binascii.hexlify(user_agent_hash_ctx.digest())

                async with httpx.AsyncClient() as client:
                    query_params = {
                        "secret": constants.HCAPTCHA_API_SECRET,
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

            if constants.FormFeatures.REQUIRES_LOGIN.value in form.features:
                if request.user.is_authenticated:
                    response["user"] = request.user.payload
                    response["user"]["admin"] = request.user.admin

                    if (
                            constants.FormFeatures.COLLECT_EMAIL.value in form.features
                            and "email" not in response["user"]
                    ):
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
                    if not question.required:
                        response["response"][question.id] = None
                    else:
                        missing_fields.append(question.id)

            if missing_fields:
                return JSONResponse({
                    "error": "missing_fields",
                    "fields": missing_fields
                }, status_code=400)

            try:
                response_obj = FormResponse(**response)
            except ValidationError as e:
                return JSONResponse(e.errors(), status_code=422)

            # Run unittests if needed
            if any("unittests" in question.data for question in form.questions):
                unittest_results = await execute_unittest(response_obj, form)

                if not all(test.passed for test in unittest_results):
                    # Return 500 if we encountered an internal error (code 99).
                    status_code = 500 if any(
                        test.return_code == 99 for test in unittest_results
                    ) else 403

                    return JSONResponse({
                        "error": "failed_tests",
                        "test_results": [
                            test._asdict() for test in unittest_results if not test.passed
                        ]
                    }, status_code=status_code)

            await request.state.db.responses.insert_one(
                response_obj.dict(by_alias=True)
            )

            tasks = BackgroundTasks()
            if constants.FormFeatures.WEBHOOK_ENABLED.value in form.features:
                tasks.add_task(
                    self.send_submission_webhook,
                    form=form,
                    response=response_obj,
                    request_user=request.user
                )

            if constants.FormFeatures.ASSIGN_ROLE.value in form.features:
                tasks.add_task(
                    self.assign_role,
                    form=form,
                    request_user=request.user
                )

            return JSONResponse({
                "form": form.dict(admin=False),
                "response": response_obj.dict()
            }, background=tasks)

        else:
            return JSONResponse({
                "error": "Open form not found"
            }, status_code=404)

    @staticmethod
    async def send_submission_webhook(
            form: Form,
            response: FormResponse,
            request_user: User
    ) -> None:
        """Helper to send a submission message to a discord webhook."""
        # Stop if webhook is not available
        if form.webhook is None:
            raise ValueError("Got empty webhook.")

        try:
            mention = request_user.discord_mention
        except AttributeError:
            mention = "User"

        user = response.user

        # Build Embed
        embed = {
            "title": "New Form Response",
            "description": f"{mention} submitted a response to `{form.name}`.",
            "url": f"{constants.FRONTEND_URL}/form/{form.id}/{response.id}",
            "timestamp": response.timestamp,
            "color": 7506394,
        }

        # Add author to embed
        if request_user.is_authenticated:
            embed["author"] = {"name": request_user.display_name}

            if user and user.avatar:
                url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.png"
                embed["author"]["icon_url"] = url

        # Build Hook
        hook = {
            "embeds": [embed],
            "allowed_mentions": {"parse": ["users", "roles"]},
            "username": form.name or "Python Discord Forms"
        }

        # Set hook message
        message = form.webhook.message
        if message:
            # Available variables, see SCHEMA.md
            ctx = {
                "user": mention,
                "response_id": response.id,
                "form": form.name,
                "form_id": form.id,
                "time": response.timestamp,
            }

            for key in ctx:
                message = message.replace(f"{{{key}}}", str(ctx[key]))

            hook["content"] = message.replace("_USER_MENTION_", mention)

        # Post hook
        async with httpx.AsyncClient() as client:
            r = await client.post(form.webhook.url, json=hook)
            r.raise_for_status()

    @staticmethod
    async def assign_role(form: Form, request_user: User) -> None:
        """Assigns Discord role to user when user submitted response."""
        if not form.discord_role:
            raise ValueError("Got empty Discord role ID.")

        url = (
            f"{constants.DISCORD_API_BASE_URL}/guilds/{constants.DISCORD_GUILD}"
            f"/members/{request_user.payload['id']}/roles/{form.discord_role}"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.put(url, headers=DISCORD_HEADERS)
            # Handle Rate Limits
            while resp.status_code == 429:
                retry_after = float(resp.headers["X-Ratelimit-Reset-After"])
                await asyncio.sleep(retry_after)
                resp = await client.put(url, headers=DISCORD_HEADERS)

            resp.raise_for_status()
