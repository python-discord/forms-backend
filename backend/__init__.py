import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend.authentication import JWTAuthenticationBackend
from backend.route_manager import create_route_map
from backend.middleware import DatabaseMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        # TODO: Convert this into a RegEx that works for prod, netlify & previews
        allow_origins=["*"],
        allow_headers=[
            "Authorization",
            "Content-Type"
        ],
        allow_methods=["*"]
    ),
    Middleware(DatabaseMiddleware),
    Middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend())
]

app = Starlette(routes=create_route_map(), middleware=middleware)
