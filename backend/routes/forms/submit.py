"""
Submit a form.
"""

import asyncio
import binascii
import datetime
import hashlib
import typing
import uuid
from typing import Any, Optional

import httpx
import pymongo.database
import sentry_sdk
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
from backend.routes.forms.discover import AUTH_FORM
from backend.routes.forms.unittesting import BypassDetectedError, execute_unittest
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


class UnittestError(BaseModel):
    question_id: str
    question_index: int
    return_code: int
    passed: bool
    result: str


class UnittestErrorMessage(ErrorMessage):
    test_results: list[UnittestError]


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
            HTTP_400=ErrorMessage,
            HTTP_422=UnittestErrorMessage
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
                await request.user.refresh_data(request.state.db)

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

        form_id = request.path_params["form_id"]

        if form_id == AUTH_FORM.id:
            response = FormResponse(
                id="not-submitted",
                form_id=AUTH_FORM.id,
                response={question.id: None for question in AUTH_FORM.questions},
                timestamp=datetime.datetime.now().isoformat()
            ).dict()
            return JSONResponse({"form": AUTH_FORM.dict(admin=False), "response": response})

        if form := await request.state.db.forms.find_one({"_id": form_id, "features": "OPEN"}):
            form = Form(**form)
            response = data.copy()
            response["id"] = str(uuid.uuid4())
            response["form_id"] = form.id

            if constants.FormFeatures.DISABLE_ANTISPAM.value not in form.features:
                ip_hash_ctx = hashlib.md5()
                ip_hash_ctx.update(
                    request.headers.get(
                        "Cf-Connecting-IP", request.client.host
                    ).encode()
                )
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
                unittest_results, errors = await execute_unittest(response_obj, form)

                if len(errors):
                    username = getattr(request.user, "user_id", "Unknown")
                    sentry_sdk.capture_exception(BypassDetectedError(
                        f"Detected unittest bypass attempt on form {form.id} by {username}. "
                        f"Submission has been written to reporting database ({response_obj.id})."
                    ))
                    database: pymongo.database.Database = request.state.db
                    await database.get_collection("violations").insert_one({
                        "user": username,
                        "bypasses": [error.args[0] for error in errors],
                        "submission": response_obj.dict(by_alias=True),
                        "timestamp": response_obj.timestamp,
                        "id": response_obj.id,
                    })

                failures = []
                status_code = 422

                for test in unittest_results:
                    response_obj.response[test.question_id] = {
                        "value": response_obj.response[test.question_id],
                        "passed": test.passed
                    }

                    if test.return_code == 0:
                        failure_names = [] if test.passed else test.result.split(";")
                    elif test.return_code == 5:
                        failure_names = ["Could not parse user code."]
                    elif test.return_code == 6:
                        failure_names = ["Could not load user code."]
                    elif test.return_code == 10:
                        failure_names = ["Bypass detected."]
                    else:
                        failure_names = ["Internal error."]

                    response_obj.response[test.question_id]["failures"] = failure_names

                    # Report a failure on internal errors,
                    # or if the test suite doesn't allow failures
                    if not test.passed:
                        allow_failure = (
                            form.questions[test.question_index].data["unittests"]["allow_failure"]
                        )

                        # An error while communicating with the test runner
                        if test.return_code == 99:
                            failures.append(test)
                            status_code = 500

                        elif not allow_failure:
                            failures.append(test)

                if len(failures):
                    return JSONResponse({
                        "error": "failed_tests",
                        "test_results": [
                            test._asdict() for test in failures
                        ]
                    }, status_code=status_code)

            await request.state.db.responses.insert_one(
                response_obj.dict(by_alias=True)
            )

            tasks = BackgroundTasks()
            if constants.FormFeatures.WEBHOOK_ENABLED.value in form.features:
                if constants.FormFeatures.REQUIRES_LOGIN.value in form.features:
                    request_user = request.user
                else:
                    request_user = None
                tasks.add_task(
                    self.send_submission_webhook,
                    form=form,
                    response=response_obj,
                    request_user=request_user
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
            request_user: typing.Optional[User]
    ) -> None:
        """Helper to send a submission message to a discord webhook."""
        # Stop if webhook is not available
        if form.webhook is None:
            raise ValueError("Got empty webhook.")

        try:
            mention = request_user.discord_mention
        except AttributeError:
            mention = "A user"

        # Build Embed
        embed = {
            "title": "New Form Response",
            "description": f"{mention} submitted a response to `{form.name}`.",
            "url": f"https://forms-api.pythondiscord.com/forms/{form.id}/responses/{response.id}",
            "timestamp": response.timestamp,
            "color": 7506394,
        }

        # Add author to embed
        if request_user and request_user.is_authenticated:
            user = response.user
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
