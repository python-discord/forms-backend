import typing as t

import pymongo
import ssl
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.constants import DATABASE_URL, MONGO_DATABASE


class DatabaseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: t.Callable) -> Response:
        client = pymongo.MongoClient(
            DATABASE_URL,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        db = client[MONGO_DATABASE]
        request.state.db = db
        response = await call_next(request)
        return response
