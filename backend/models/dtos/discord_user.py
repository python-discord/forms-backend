import datetime
import typing as t

from pydantic import BaseModel


class _User(BaseModel):
    """Base for discord users and members."""

    # Discord default fields.
    username: str
    id: str
    discriminator: str
    avatar: str | None
    bot: bool | None
    system: bool | None
    locale: str | None
    verified: bool | None
    email: str | None
    flags: int | None
    premium_type: int | None
    public_flags: int | None


class DiscordUser(_User):
    """Schema model of Discord user for form response."""

    # Custom fields
    admin: bool


class DiscordMember(BaseModel):
    """A discord guild member."""

    user: _User
    nick: str | None
    avatar: str | None
    roles: list[str]
    joined_at: datetime.datetime
    premium_since: datetime.datetime | None
    deaf: bool
    mute: bool
    pending: bool | None
    permissions: str | None
    communication_disabled_until: datetime.datetime | None

    def dict(self, *args, **kwargs) -> dict[str, t.Any]:
        """Convert the model to a python dict, and encode timestamps in a serializable format."""
        data = super().dict(*args, **kwargs)
        for field, value in data.items():
            if isinstance(value, datetime.datetime):
                data[field] = value.isoformat()

        return data
