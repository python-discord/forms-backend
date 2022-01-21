import typing

from pydantic import BaseModel


class RoleTags(BaseModel):
    """Meta information about a discord role."""

    bot_id: typing.Optional[str]
    integration_id: typing.Optional[str]
    premium_subscriber: bool

    def __init__(self, **data: typing.Any):
        """
        Handle the terrible discord API.

        Discord only returns the premium_subscriber field if it's true,
        meaning the typical validation process wouldn't work.

        We manually parse the raw data to determine if the field exists, and give it a useful
        bool value.
        """
        data["premium_subscriber"] = "premium_subscriber" in data.keys()
        super().__init__(**data)


class DiscordRole(BaseModel):
    """Schema model of Discord guild roles."""

    id: str
    name: str
    color: int
    hoist: bool
    icon: typing.Optional[str]
    unicode_emoji: typing.Optional[str]
    position: int
    permissions: str
    managed: bool
    mentionable: bool
    tags: typing.Optional[RoleTags]
