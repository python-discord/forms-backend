import typing as t

import jwt
from starlette.authentication import BaseUser
from starlette.requests import Request

from backend.constants import SECRET_KEY
from backend.discord import fetch_user_details


class User(BaseUser):
    """Starlette BaseUser implementation for JWT authentication."""

    def __init__(self, token: str, payload: dict[str, t.Any]) -> None:
        self.token = token
        self.payload = payload
        self.admin = False

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

    async def fetch_admin_status(self, request: Request) -> bool:
        self.admin = await request.state.db.admins.find_one(
            {"_id": self.payload["id"]}
        ) is not None

        return self.admin

    async def refresh_data(self) -> None:
        """Fetches user data from discord, and updates the instance."""
        self.payload = await fetch_user_details(self.decoded_token.get("token"))

        updated_info = self.decoded_token
        updated_info["user_details"] = self.payload

        self.token = jwt.encode(updated_info, SECRET_KEY, algorithm="HS256")
