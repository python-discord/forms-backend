import typing as t

import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.constants import DATABASE_URL, DOCS_PASSWORD, MONGO_DATABASE


class DatabaseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: t.Callable) -> Response:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            DATABASE_URL,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        db = client[MONGO_DATABASE]
        request.state.db = db
        response = await call_next(request)
        return response


class ProtectedDocsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: t.Callable) -> Response:
        if DOCS_PASSWORD and request.url.path.startswith("/docs"):
            if request.cookies.get("docs_password") != DOCS_PASSWORD:
                return JSONResponse({"status": "unauthorized"}, status_code=403)

        resp = await call_next(request)
        return resp
