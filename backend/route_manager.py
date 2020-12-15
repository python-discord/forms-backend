"""
Module to dynamically generate a Starlette routing map based on a directory tree.
"""

import importlib
import inspect
import typing as t

from pathlib import Path

from starlette.routing import Route as StarletteRoute, BaseRoute, Mount
from nested_dict import nested_dict

from backend.route import Route


def construct_route_map_from_dict(route_dict: dict) -> list[BaseRoute]:
    route_map = []
    for mount, item in route_dict.items():
        if inspect.isclass(item):
            route_map.append(StarletteRoute(mount, item))
        else:
            route_map.append(Mount(mount, routes=construct_route_map_from_dict(item)))

    # Order non-capturing routes before capturing routes
    route_map.sort(key=lambda route: "{" in route.path)

    return route_map


def is_route_class(member: t.Any) -> bool:
    return inspect.isclass(member) and issubclass(member, Route) and member != Route


def create_route_map() -> list[BaseRoute]:
    routes_directory = Path("backend") / "routes"

    route_dict = nested_dict()

    for file in routes_directory.rglob("*.py"):
        import_name = f"{str(file.parent).replace('/', '.')}.{file.stem}"

        route = importlib.import_module(import_name)

        for _member_name, member in inspect.getmembers(route):
            if is_route_class(member):
                member.check_parameters()

                levels = str(file.parent).split("/")[2:]

                current_level = None
                for level in levels:
                    if current_level is None:
                        current_level = route_dict[f"/{level}"]
                    else:
                        current_level = current_level[f"/{level}"]

                if current_level is not None:
                    current_level[member.path] = member
                else:
                    route_dict[member.path] = member

    return construct_route_map_from_dict(route_dict.to_dict())
