"""
Submit a form.
"""

import binascii
import hashlib

import jwt
from starlette.requests import Request

from starlette.responses import JSONResponse

from backend.constants import SECRET_KEY
from backend.route import Route


class SubmitForm(Route):
    """
    Submit a form with the provided form ID.
    """

    name = "submit_form"
    path = "/submit/{form_id:str}"

    async def post(self, request: Request) -> JSONResponse:
        data = await request.json()

        if form := request.state.db.forms.find_one(
            {"_id": request.path_params["form_id"], "features": "OPEN"}
        ):
            response_obj = {}

            if "DISABLE_ANTISPAM" not in form["features"]:
                ip_hash_ctx = hashlib.md5()
                ip_hash_ctx.update(request.client.host.encode())
                ip_hash = binascii.hexlify(ip_hash_ctx.digest())

                response_obj["antispam"] = {
                    "ip": ip_hash.decode()
                }

            if "REQUIRES_LOGIN" in form["features"]:
                if token := data.get("token"):
                    data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                    response_obj["user"] = {
                        "user": f"{data['username']}#{data['discriminator']}",
                        "id": data["id"]
                    }

                    if "COLLECT_EMAIL" in form["features"]:
                        if data.get("email"):
                            response_obj["user"]["email"] = data["email"]
                        else:
                            return JSONResponse({
                                "error": "User data did not include email information"
                            })
                else:
                    return JSONResponse({
                        "error": "Missing Discord user data"
                    })

            return JSONResponse({
                "form": form,
                "response": response_obj
            })
        else:
            return JSONResponse({
                "error": "Open form not found"
            })
