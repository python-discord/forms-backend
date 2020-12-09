import typing as t

from pydantic import BaseModel, Field

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
