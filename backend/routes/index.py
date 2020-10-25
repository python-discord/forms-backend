"""
Index route for the forms API.
"""

from starlette.responses import JSONResponse

from backend.route import Route


class IndexRoute(Route):
    """
    Return a generic hello world message with some information to the client.

    Can be used as a healthcheck for Kubernetes or a frontend connection check.
    """

    name = "index"
    path = "/"

    def get(self, request):
        return JSONResponse({
            "message": "Hello, world!",
            "client": request.client.host
        })
