import typing as t

import httpx
from pydantic import BaseModel, Field, validator

from backend.constants import FormFeatures
from .question import Question

PUBLIC_FIELDS = ["id", "features", "questions", "name", "description"]


class _WebHook(BaseModel):
    """Schema model of discord webhooks."""
    url: str
    message: t.Optional[str]

    @validator("url")
    def validate_url(cls, url: str) -> str:
        """Checks if discord webhook urls are valid."""
        if not isinstance(url, str):
            raise ValueError("Webhook URL must be a string.")

        if "discord.com/api/webhooks/" not in url:
            raise ValueError("URL must be a discord webhook.")

        # Attempt to connect to URL
        try:
            httpx.get(url).raise_for_status()

        except httpx.RequestError as e:
            # Catch exceptions in request format
            raise ValueError(
                f"Encountered error while trying to connect to url: `{e}`"
            )

        except httpx.HTTPStatusError as e:
            # Catch exceptions in response
            status = e.response.status_code

            if status == 401:
                raise ValueError(
                    "Could not authenticate with target. Please check the webhook url."
                )
            elif status == 404:
                raise ValueError(
                    "Target could not find webhook url. Please check the webhook url."
                )
            else:
                raise ValueError(
                    f"Unknown error ({status}) while connecting to target: {e}"
                )

        return url


class _FormMeta(BaseModel):
    """Schema model for form meta data."""
    webhook: _WebHook = None


class Form(BaseModel):
    """Schema model for form."""

    id: str = Field(alias="_id")
    features: list[str]
    questions: list[Question]
    name: str
    description: str
    meta: _FormMeta

    class Config:
        allow_population_by_field_name = True

    @validator("features")
    def validate_features(cls, value: list[str]) -> t.Optional[list[str]]:
        """Validates is all features in allowed list."""
        # Uppercase everything to avoid mixed case in DB
        value = [v.upper() for v in value]
        allowed_values = [v.value for v in FormFeatures.__members__.values()]
        if any(v not in allowed_values for v in value):
            raise ValueError("Form features list contains one or more invalid values.")

        if FormFeatures.COLLECT_EMAIL in value and FormFeatures.REQUIRES_LOGIN not in value:  # noqa
            raise ValueError("COLLECT_EMAIL feature require REQUIRES_LOGIN feature.")

        return value

    def dict(self, admin: bool = True, **kwargs: t.Any) -> dict[str, t.Any]:
        """Wrapper for original function to exclude private data for public access."""
        data = super().dict(**kwargs)

        returned_data = {}

        if not admin:
            for field in PUBLIC_FIELDS:
                if field == "id" and kwargs.get("by_alias"):
                    fetch_field = "_id"
                else:
                    fetch_field = field

                returned_data[field] = data[fetch_field]
        else:
            returned_data = data

        return returned_data
