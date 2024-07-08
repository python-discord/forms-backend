import datetime
import typing as t

from pydantic import BaseModel, Field, validator

from .antispam import AntiSpam
from .discord_user import DiscordUser


class FormResponse(BaseModel):
    """Schema model for form response."""

    id: str = Field(alias="_id")
    user: DiscordUser | None
    antispam: AntiSpam | None
    response: dict[str, t.Any]
    form_id: str
    timestamp: str

    @validator("timestamp", pre=True)
    def set_timestamp(cls, iso_string: str | None) -> str:
        if iso_string is None:
            return datetime.datetime.now(tz=datetime.UTC).isoformat()

        if not isinstance(iso_string, str):
            msg = "Submission timestamp must be a string."
            raise TypeError(msg)

        # Convert to datetime and back to ensure string is valid
        return datetime.datetime.fromisoformat(iso_string).isoformat()

    class Config:
        allow_population_by_field_name = True


class ResponseList(BaseModel):
    __root__: list[FormResponse]
