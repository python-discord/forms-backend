import typing as t

import httpx
from pydantic import BaseModel, Field, constr, root_validator, validator
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from backend.constants import DISCORD_GUILD, FormFeatures, WebHook

from .question import Question

PUBLIC_FIELDS = [
    "id",
    "features",
    "questions",
    "name",
    "description",
    "submitted_text",
    "discord_role",
]


class _WebHook(BaseModel):
    """Schema model of discord webhooks."""

    url: str
    message: str | None
    thread_id: str | None = None

    @validator("url")
    def validate_url(cls, url: str) -> str:
        """Validates URL parameter."""
        if "discord.com/api/webhooks/" not in url:
            msg = "URL must be a discord webhook."
            raise ValueError(msg)

        return url

    @validator("thread_id")
    def validate_thread_id(cls, thread_id: str | None) -> str | None:
        """Validates thread_id parameter."""
        if thread_id is not None and not thread_id.isdigit():
            msg = "Thread ID must be a string of digits."
            raise ValueError(msg)

        return thread_id


class Form(BaseModel):
    """Schema model for form."""

    id: constr(to_lower=True) = Field(alias="_id")
    features: list[str]
    questions: list[Question]
    name: str
    description: str
    submitted_text: str | None = None
    webhook: _WebHook = None
    discord_role: str | None
    response_readers: list[str] | None
    editors: list[str] | None

    class Config:
        allow_population_by_field_name = True

    @validator("features")
    def validate_features(cls, value: list[str]) -> list[str]:
        """Validates is all features in allowed list."""
        # Uppercase everything to avoid mixed case in DB
        value = [v.upper() for v in value]
        allowed_values = [v.value for v in FormFeatures.__members__.values()]
        if any(v not in allowed_values for v in value):
            msg = "Form features list contains one or more invalid values."
            raise ValueError(msg)

        if FormFeatures.REQUIRES_LOGIN.value not in value:
            if FormFeatures.COLLECT_EMAIL.value in value:
                msg = "COLLECT_EMAIL feature require REQUIRES_LOGIN feature."
                raise ValueError(msg)

            if FormFeatures.ASSIGN_ROLE.value in value:
                msg = "ASSIGN_ROLE feature require REQUIRES_LOGIN feature."
                raise ValueError(msg)

        return value

    @validator("response_readers", "editors")
    def validate_role_scoping(cls, value: list[str] | None) -> list[str]:
        """Ensure special role based permissions aren't granted to the @everyone role."""
        if value and DISCORD_GUILD in value:
            msg = "You can not add the everyone role as an access scope."
            raise ValueError(msg)
        return value

    @root_validator
    def validate_role(cls, values: dict[str, t.Any]) -> dict[str, t.Any]:
        """Validates does Discord role provided when flag provided."""
        is_role_assigner = FormFeatures.ASSIGN_ROLE.value in values.get("features", [])
        if is_role_assigner and not values.get("discord_role"):
            msg = "discord_role field is required when ASSIGN_ROLE flag is provided."
            raise ValueError(msg)

        return values

    def dict(self, admin: bool = True, **kwargs) -> dict[str, t.Any]:  # noqa: FBT001, FBT002
        """Wrapper for original function to exclude private data for public access."""
        data = super().dict(**kwargs)
        if admin:
            return data

        returned_data = {}

        for field in PUBLIC_FIELDS:
            fetch_field = "_id" if field == "id" and kwargs.get("by_alias") else field
            returned_data[field] = data[fetch_field]

        # Replace the unittest data section of code questions with the number of test cases.
        for question in returned_data["questions"]:
            if question["type"] == "code" and question["data"]["unittests"] is not None:
                question["data"]["unittests"]["tests"] = len(question["data"]["unittests"]["tests"])
        return returned_data


class FormList(BaseModel):
    __root__: list[Form]


async def validate_hook_url(url: str) -> ValidationError | None:
    """Validator for discord webhook urls."""

    async def validate() -> str | None:
        if not isinstance(url, str):
            msg = "Webhook URL must be a string."
            raise TypeError(msg)

        if "discord.com/api/webhooks/" not in url:
            msg = "URL must be a discord webhook."
            raise ValueError(msg)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()

        except httpx.RequestError as error:
            # Catch exceptions in request format
            msg = f"Encountered error while trying to connect to url: `{error}`"
            raise ValueError(msg)

        except httpx.HTTPStatusError as error:
            # Catch exceptions in response
            status = error.response.status_code

            if status == 401:
                msg = "Could not authenticate with target. Please check the webhook url."
                raise ValueError(msg)
            if status == 404:
                msg = "Target could not find webhook url. Please check the webhook url."
                raise ValueError(msg)

            msg = f"Unknown error ({status}) while connecting to target: {error}"
            raise ValueError(msg)

        return url

    # Validate, and return errors, if any
    try:
        await validate()
    except Exception as e:  # noqa: BLE001
        loc = (
            WebHook.__name__.lower(),
            WebHook.URL.value,
        )

        return ValidationError([ErrorWrapper(e, loc=loc)], _WebHook)
