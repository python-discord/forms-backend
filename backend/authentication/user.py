import typing
import typing as t

import jwt
from pymongo.database import Database
from starlette.authentication import BaseUser

from backend import discord, models
from backend.constants import SECRET_KEY


class User(BaseUser):
    """Starlette BaseUser implementation for JWT authentication."""

    def __init__(
        self,
        token: str,
        payload: dict[str, t.Any],
        member: typing.Optional[models.DiscordMember],
    ) -> None:
        self.token = token
        self.payload = payload
        self.admin = False
        self.member = member

    @property
    def is_authenticated(self) -> bool:
        """Returns True because user is always authenticated at this stage."""
        return True

    @property
    def display_name(self) -> str:
        """Return username and discriminator as display name."""
        return f"{self.payload['username']}#{self.payload['discriminator']}"

    @property
    def discord_mention(self) -> str:
        return f"<@{self.payload['id']}>"

    @property
    def decoded_token(self) -> dict[str, any]:
        return jwt.decode(self.token, SECRET_KEY, algorithms=["HS256"])

    async def get_user_roles(self, database: Database) -> list[str]:
        """Get a list of the user's discord roles."""
        if not self.member:
            return []

        server_roles = await discord.get_roles(database)
        roles = [role.name for role in server_roles if role.id in self.member.roles]

        if "admin" in roles:
            # Protect against collision with the forms admin role
            roles.remove("admin")
            roles.append("discord admin")

        return roles

    async def fetch_admin_status(self, database: Database) -> bool:
        self.admin = await database.admins.find_one(
            {"_id": self.payload["id"]}
        ) is not None

        return self.admin

    async def refresh_data(self, database: Database) -> None:
        """Fetches user data from discord, and updates the instance."""
        self.member = await discord.get_member(database, self.payload["id"])

        if self.member:
            self.payload = self.member.user.dict()
        else:
            self.payload = await discord.fetch_user_details(self.decoded_token.get("token"))

        updated_info = self.decoded_token
        updated_info["user_details"] = self.payload

        self.token = jwt.encode(updated_info, SECRET_KEY, algorithm="HS256")
