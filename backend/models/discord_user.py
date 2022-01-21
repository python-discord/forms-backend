import datetime
import typing as t

from pydantic import BaseModel


class _User(BaseModel):
    """Base for discord users and members."""

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


class DiscordUser(_User):
    """Schema model of Discord user for form response."""

    # Custom fields
    admin: bool


class DiscordMember(BaseModel):
    """A discord guild member."""

    user: _User
    nick: t.Optional[str]
    avatar: t.Optional[str]
    roles: list[str]
    joined_at: datetime.datetime
    premium_since: t.Optional[datetime.datetime]
    deaf: bool
    mute: bool
    pending: t.Optional[bool]
    permissions: t.Optional[str]
    communication_disabled_until: t.Optional[datetime.datetime]
