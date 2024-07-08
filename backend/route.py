"""Base class for implementing dynamic routing."""

from starlette.endpoints import HTTPEndpoint


class Route(HTTPEndpoint):
    name: str
    path: str

    @classmethod
    def check_parameters(cls) -> None:
        if not hasattr(cls, "name"):
            msg = f"Route {cls.__name__} has not defined a name"
            raise ValueError(msg)

        if not hasattr(cls, "path"):
            msg = f"Route {cls.__name__} has not defined a path"
            raise ValueError(msg)
