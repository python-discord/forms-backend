import jwt
import typing as t
from abc import ABC

from starlette import authentication
from starlette.requests import Request

from backend import constants
# We must import user such way here to avoid circular imports
from .user import User


class JWTAuthenticationBackend(authentication.AuthenticationBackend, ABC):
    """Custom Starlette authentication backend for JWT."""

    @staticmethod
    def get_token_from_header(header: str) -> t.Optional[str]:
        """Parse JWT token from header value."""
        try:
            prefix, token = header.split()
        except ValueError:
            raise authentication.AuthenticationError(
                "Unable to split prefix and token from Authorization header."
            )

        if prefix.upper() != "JWT":
            raise authentication.AuthenticationError(
                f"Invalid Authorization header prefix '{prefix}'."
            )

        return token

    async def authenticate(
        self, request: Request
    ) -> t.Optional[t.Tuple[authentication.AuthCredentials, authentication.BaseUser]]:
        """Handles JWT authentication process."""
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        token = self.get_token_from_header(auth)

        try:
            payload = jwt.decode(token, constants.SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            raise authentication.AuthenticationError(str(e))

        scopes = ["authenticated"]

        if payload.get("admin", False) is True:
            scopes.append("admin")

        return authentication.AuthCredentials(scopes), User(token, payload)
