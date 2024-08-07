from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.constants import DATABASE_URL, DOCS_PASSWORD, MONGO_DATABASE


class DatabaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            DATABASE_URL,
            tlsAllowInvalidCertificates=True,
        )
        db = client[MONGO_DATABASE]
        Request(scope).state.db = db
        await self._app(scope, receive, send)


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
