import datetime
import typing as t

from pydantic import BaseModel, Field, validator

from .antispam import AntiSpam
from .discord_user import DiscordUser


class FormResponse(BaseModel):
    """Schema model for form response."""

    id: str = Field(alias="_id")
    user: t.Optional[DiscordUser]
    antispam: t.Optional[AntiSpam]
    response: dict[str, t.Any]
    form_id: str
    timestamp: str

    @validator("timestamp", pre=True)
    def set_timestamp(cls, iso_string: t.Optional[str]) -> t.Optional[str]:
        if iso_string is None:
            return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        elif not isinstance(iso_string, str):
            raise ValueError("Submission timestamp must be a string.")

        # Convert to datetime and back to ensure string is valid
        return datetime.datetime.fromisoformat(iso_string).isoformat()

    class Config:
        allow_population_by_field_name = True


class ResponseList(BaseModel):
    __root__: t.List[FormResponse]
