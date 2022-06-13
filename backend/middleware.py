import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

from backend.constants import DATABASE_URL, DOCS_PASSWORD, MONGO_DATABASE


class DatabaseMiddleware:

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            DATABASE_URL,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        db = client[MONGO_DATABASE]
        scope["state"].db = db
        await self._app(scope, send, receive)


class ProtectedDocsMiddleware:

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope)
        if DOCS_PASSWORD and request.url.path.startswith("/docs"):
            if request.cookies.get("docs_password") != DOCS_PASSWORD:
                resp = JSONResponse({"status": "unauthorized"}, status_code=403)
                await resp(scope, receive, send)
                return
        await self._app(scope, receive, send)
