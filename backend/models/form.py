import typing as t

import httpx
from pydantic import BaseModel, Field, root_validator, validator
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from backend.constants import FormFeatures, WebHook
from .question import Question

PUBLIC_FIELDS = [
    "id",
    "features",
    "questions",
    "name",
    "description",
    "submitted_text",
    "discord_role"
]


class _WebHook(BaseModel):
    """Schema model of discord webhooks."""
    url: str
    message: t.Optional[str]

    @validator("url")
    def validate_url(cls, url: str) -> str:
        """Validates URL parameter."""
        if "discord.com/api/webhooks/" not in url:
            raise ValueError("URL must be a discord webhook.")

        return url


class Form(BaseModel):
    """Schema model for form."""

    id: str = Field(alias="_id")
    features: list[str]
    questions: list[Question]
    name: str
    description: str
    submitted_text: t.Optional[str] = None
    webhook: _WebHook = None
    discord_role: t.Optional[str]

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

        if FormFeatures.REQUIRES_LOGIN.value not in value:
            if FormFeatures.COLLECT_EMAIL.value in value:
                raise ValueError(
                    "COLLECT_EMAIL feature require REQUIRES_LOGIN feature."
                )

            if FormFeatures.ASSIGN_ROLE.value in value:
                raise ValueError("ASSIGN_ROLE feature require REQUIRES_LOGIN feature.")

        return value

    @root_validator
    def validate_role(cls, values: dict[str, t.Any]) -> t.Optional[dict[str, t.Any]]:
        """Validates does Discord role provided when flag provided."""
        if FormFeatures.ASSIGN_ROLE.value in values.get("features", []) and not values.get("discord_role"):  # noqa
            raise ValueError(
                "discord_role field is required when ASSIGN_ROLE flag is provided."
            )

        return values

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


class FormList(BaseModel):
    __root__: t.List[Form]


async def validate_hook_url(url: str) -> t.Optional[ValidationError]:
    """Validator for discord webhook urls."""
    async def validate() -> t.Optional[str]:
        if not isinstance(url, str):
            raise ValueError("Webhook URL must be a string.")

        if "discord.com/api/webhooks/" not in url:
            raise ValueError("URL must be a discord webhook.")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()

        except httpx.RequestError as error:
            # Catch exceptions in request format
            raise ValueError(
                f"Encountered error while trying to connect to url: `{error}`"
            )

        except httpx.HTTPStatusError as error:
            # Catch exceptions in response
            status = error.response.status_code

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
                    f"Unknown error ({status}) while connecting to target: {error}"
                )

        return url

    # Validate, and return errors, if any
    try:
        await validate()
    except Exception as e:
        loc = (
            WebHook.__name__.lower(),
            WebHook.URL.value
        )

        return ValidationError([ErrorWrapper(e, loc=loc)], _WebHook)
