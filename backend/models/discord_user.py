import typing as t

from pydantic import BaseModel


class DiscordUser(BaseModel):
    """Schema model of Discord user for form response."""

    # Discord default fields.
    username: str
    id: str
    discriminator: str
    avatar: t.Optional[str]
    bot: t.Optional[bool]
    system: t.Optional[bool]
    locale: t.Optional[str]
    verified: t.Optional[bool]
    email: t.Optional[str]
    flags: t.Optional[int]
    premium_type: t.Optional[int]
    public_flags: t.Optional[int]

    # Custom fields
    admin: bool
