import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend import constants
from backend.authentication import JWTAuthenticationBackend
from backend.route_manager import create_route_map
from backend.middleware import DatabaseMiddleware, ProtectedDocsMiddleware
from backend.validation import api

sentry_sdk.init(
    dsn=constants.FORMS_BACKEND_DSN,
    send_default_pii=True,
    release=f"forms-backend@{constants.GIT_SHA}"
)

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
    Middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend()),
    Middleware(SentryAsgiMiddleware),
    Middleware(ProtectedDocsMiddleware),
]

app = Starlette(routes=create_route_map(), middleware=middleware)
api.register(app)
