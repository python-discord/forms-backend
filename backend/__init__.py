import logging

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend import constants
from backend import logs  # This has to be imported before other logging statements
from backend.authentication import JWTAuthenticationBackend
from backend.middleware import DatabaseMiddleware, ProtectedDocsMiddleware
from backend.route_manager import create_route_map
from backend.validation import api

ORIGINS = [
    r"(https://[^.?#]*--pydis-forms\.netlify\.app)",  # Netlify Previews
    r"(https?://[^.?#]*.forms-frontend.pages.dev)",  # Cloudflare Previews
]

if not constants.PRODUCTION:
    # Allow all hosts on non-production deployments
    ORIGINS.append(r"(.*)")

ALLOW_ORIGIN_REGEX = "|".join(ORIGINS)

sentry_sdk.init(
    dsn=constants.FORMS_BACKEND_DSN,
    send_default_pii=True,
    release=f"forms-backend@{constants.GIT_SHA}"
)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://forms.pythondiscord.com"],
        allow_origin_regex=ALLOW_ORIGIN_REGEX,
        allow_headers=[
            "Content-Type"
        ],
        allow_methods=["*"],
        allow_credentials=True
    ),
    Middleware(DatabaseMiddleware),
    Middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend()),
    Middleware(SentryAsgiMiddleware),
    Middleware(ProtectedDocsMiddleware),
]

app = Starlette(routes=create_route_map(), middleware=middleware)
api.register(app)
