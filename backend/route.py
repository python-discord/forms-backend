"""
Base class for implementing dynamic routing.
"""
from starlette.endpoints import HTTPEndpoint


class Route(HTTPEndpoint):
    name: str
    path: str

    @classmethod
    def check_parameters(cls):
        if not hasattr(cls, "name"):
            raise ValueError(f"Route {cls.__name__} has not defined a name")

        if not hasattr(cls, "path"):
            raise ValueError(f"Route {cls.__name__} has not defined a path")
