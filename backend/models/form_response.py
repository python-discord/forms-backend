import typing as t

from pydantic import BaseModel, Field, root_validator

from backend.constants import FormFeatures
from .antispam import AntiSpam
from .discord_user import DiscordUser


class FormResponse(BaseModel):
    """Schema model for form response."""

    id: str = Field(alias="_id")
    user: t.Optional[DiscordUser]
    antispam: t.Optional[AntiSpam]
    response: t.Dict[str, t.Any]
    form_id: str

    class Config:
        allow_population_by_field_name = True

    @root_validator
    def validate_data(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Validates is all required (based on flags) is provided."""
        flags = values.get("flags", [])

        if FormFeatures.DISABLE_ANTISPAM not in flags and values.get("antispam") is None:  # noqa
            raise ValueError("Antispam information required.")

        if FormFeatures.REQUIRES_LOGIN in flags:
            if values.get("user") is None:
                raise ValueError("User information required.")

            values["user"]["require_email"] = FormFeatures.COLLECT_EMAIL in flags

        return values
