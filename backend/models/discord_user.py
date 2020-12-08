import typing as t

from pydantic import BaseModel, root_validator


class DiscordUser(BaseModel):
    """Schema model of Discord user for form response."""

    # Discord default fields
    id: int  # This is actually snowflake, but we simplify it here
    username: str
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

    @root_validator
    def validate_data(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Validates email data when email collection is required."""
        if values.get("require_email", False) is True:
            if values.get("email") is None or values.get("verified") is None:
                raise ValueError("Email information about user is required.")

        return values
