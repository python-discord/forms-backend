import typing as t

from starlette.authentication import BaseUser


class User(BaseUser):
    """Starlette BaseUser implementation for JWT authentication."""

    def __init__(self, token: str, payload: dict[str, t.Any]) -> None:
        self.token = token
        self.payload = payload

    @property
    def is_authenticated(self) -> bool:
        """Returns True because user is always authenticated at this stage."""
        return True

    @property
    def display_name(self) -> str:
        """Return username and discriminator as display name."""
        return f"{self.payload['username']}#{self.payload['discriminator']}"
