"""
Index route for the forms API.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.route import Route


class IndexRoute(Route):
    """
    Return a generic hello world message with some information to the client.

    Can be used as a healthcheck for Kubernetes or a frontend connection check.
    """

    name = "index"
    path = "/"

    def get(self, request: Request) -> JSONResponse:
        response_data = {
            "message": "Hello, world!",
            "client": request.client.host,
            "user": {
                "authenticated": False
            }
        }

        if request.user.is_authenticated:
            response_data["user"] = {
                "authenticated": True,
                "user": request.user.payload,
                "scopes": request.auth.scopes
            }

        return JSONResponse(response_data)
