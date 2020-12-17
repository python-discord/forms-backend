"""
Submit a form.
"""

import binascii
import hashlib
import uuid

import httpx
import pydnsbl
from pydantic import ValidationError
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.constants import FRONTEND_URL, FormFeatures, HCAPTCHA_API_SECRET
from backend.models import Form, FormResponse
from backend.route import Route

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
HCAPTCHA_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}


class SubmitForm(Route):
    """
    Submit a form with the provided form ID.
    """

    name = "submit_form"
    path = "/submit/{form_id:str}"

    async def post(self, request: Request) -> JSONResponse:
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

                dsn_checker = pydnsbl.DNSBLIpChecker()
                dsn_blacklist = await dsn_checker.check_async(request.client.host)

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
                    "captcha_pass": captcha_data["success"],
                    "dns_blacklisted": dsn_blacklist.blacklisted,
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

            send_webhook = None
            if FormFeatures.WEBHOOK_ENABLED.value in form.features:
                send_webhook = BackgroundTask(
                    self.send_submission_webhook,
                    form=form,
                    response=response_obj
                )

            return JSONResponse({
                "form": form.dict(admin=False),
                "response": response_obj.dict()
            }, background=send_webhook)

        else:
            return JSONResponse({
                "error": "Open form not found"
            })

    @staticmethod
    def send_submission_webhook(form: Form, response: FormResponse) -> None:
        """Helper to send a submission message to a discord webhook."""
        # Stop if webhook is not available
        if form.meta.webhook is None:
            raise ValueError("Got empty webhook.")

        user = response.user
        username = f"{user.username}#{user.discriminator}" if user else None
        user_mention = f"<@{user.id}>" if user else f"{username or 'User'}"

        # Build Embed
        embed = {
            "title": "New Form Response",
            "description": f"{user_mention} submitted a response.",
            "url": f"{FRONTEND_URL}/path_to_view_form/{response.id}",  # noqa # TODO: Enter Form View URL
            "timestamp": response.timestamp,
            "color": 7506394,
        }

        # Add author to embed
        if user is not None:
            embed["author"] = {"name": username}

            if user.avatar is not None:
                url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.png"
                embed["author"]["icon_url"] = url

        # Build Hook
        hook = {
            "embeds": [embed],
            "allowed_mentions": {"parse": ["users", "roles"]},
            "username": form.name or "Python Discord Forms"
        }

        # Set hook message
        message = form.meta.webhook.message
        if message:
            hook["content"] = message.replace("_USER_MENTION_", f"<@{user.id}>")

        # Post hook
        httpx.post(form.meta.webhook.url, json=hook).raise_for_status()
