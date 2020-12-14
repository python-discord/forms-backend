import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend.authentication import JWTAuthenticationBackend
from backend.route_manager import create_route_map
from backend.middleware import DatabaseMiddleware

HOSTS_REGEX = r"https://(?:(?:(?:.*--)?pydis-forms\.netlify\.app)|forms\.pythondiscord\.com)"
HAS_CUSTOM_HOST = os.getenv("ALLOWED_URL") is not None

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("ALLOWED_URL")] if HAS_CUSTOM_HOST else None,
        allow_origin_regex=HOSTS_REGEX if not HAS_CUSTOM_HOST else None,
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
