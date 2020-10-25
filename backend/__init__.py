from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from backend.route_manager import create_route_map
from backend.middleware import DatabaseMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://forms.pythondiscord.com"
        ],
        allow_headers=[
            "Authorization",
            "Content-Type"
        ],
        allow_methods=["*"]
    ),
    Middleware(DatabaseMiddleware)
]

app = Starlette(routes=create_route_map(), middleware=middleware)
