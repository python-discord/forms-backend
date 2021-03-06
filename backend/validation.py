"""Utilities for providing API payload validation."""

from pydantic.fields import Field
from pydantic.main import BaseModel
from spectree import SpecTree

api = SpecTree(
    "starlette",
    TITLE="Python Discord Forms",
    PATH="docs"
)


class ErrorMessage(BaseModel):
    error: str = Field(description="The details on the error")


class OkayResponse(BaseModel):
    status: str = "ok"
