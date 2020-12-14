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
        allow_origins=[
            os.getenv("ALLOWED_URL", "https://forms.pythondiscord.com"),
        ],
        allow_origin_regex=r"https://(?:.*--)?pydis-forms\.netlify\.app/",
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
