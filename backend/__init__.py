import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import constants
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

SENTRY_RELEASE = f"forms-backend@{constants.GIT_SHA}"
sentry_sdk.init(
    dsn=constants.FORMS_BACKEND_DSN,
    send_default_pii=True,
    release=SENTRY_RELEASE,
    environment=SENTRY_RELEASE,
)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://forms.pythondiscord.com"],
        allow_origin_regex=ALLOW_ORIGIN_REGEX,
        allow_headers=[
            "Content-Type",
        ],
        allow_methods=["*"],
        allow_credentials=True,
    ),
    Middleware(DatabaseMiddleware),
    Middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend()),
    Middleware(SentryAsgiMiddleware),
    Middleware(ProtectedDocsMiddleware),
]


async def http_exception(_request: Request, exc: HTTPException) -> JSONResponse:  # noqa: RUF029
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


exception_handlers = {HTTPException: http_exception}

app = Starlette(
    routes=create_route_map(), middleware=middleware, exception_handlers=exception_handlers
)
api.register(app)
