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
    timestamp: str = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    @validator("timestamp")
    def set_timestamp(cls, _: str) -> str:
        return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    class Config:
        allow_population_by_field_name = True
