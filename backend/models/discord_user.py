import typing as t

from pydantic import BaseModel, validator


class DiscordUser(BaseModel):
    """Schema model of Discord user for form response."""

    # Discord default fields.
    username: str
    # Store ID as str not as int because JavaScript
    # doesn't work correctly with big ints.
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

    @validator("id", pre=True)
    def validate_id(cls, value: t.Any) -> t.Any:
        """When ID is integer, convert it to string."""
        if isinstance(value, int):
            return str(value)

        return value
