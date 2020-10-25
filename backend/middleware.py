from starlette.middleware.base import BaseHTTPMiddleware
import pymongo
import ssl

from backend.constants import DATABASE_URL, MONGO_DATABASE


class DatabaseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client = pymongo.MongoClient(
            DATABASE_URL,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        db = client[MONGO_DATABASE]
        request.state.db = db
        response = await call_next(request)
        return response
