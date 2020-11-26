"""
Base class for implementing dynamic routing.
"""
from starlette.endpoints import HTTPEndpoint


class Route(HTTPEndpoint):
    name: str = None
    path: str = None

    @classmethod
    def check_parameters(cls) -> "Route":
        if cls.name is None:
            raise ValueError(f"Route {cls.__name__} has not defined a name")

        if cls.path is None:
            raise ValueError(f"Route {cls.__name__} has not defined a path")
