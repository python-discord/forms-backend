import typing as t

import jwt
from starlette import authentication
from starlette.requests import Request

from backend import constants
# We must import user such way here to avoid circular imports
from .user import User


class JWTAuthenticationBackend(authentication.AuthenticationBackend):
    """Custom Starlette authentication backend for JWT."""

    @staticmethod
    def get_token_from_cookie(cookie: str) -> str:
        """Parse JWT token from cookie."""
        try:
            prefix, token = cookie.split()
        except ValueError:
            raise authentication.AuthenticationError(
                "Unable to split prefix and token from authorization cookie."
            )

        if prefix.upper() != "JWT":
            raise authentication.AuthenticationError(
                f"Invalid authorization cookie prefix '{prefix}'."
            )

        return token

    async def authenticate(
        self, request: Request
    ) -> t.Optional[tuple[authentication.AuthCredentials, authentication.BaseUser]]:
        """Handles JWT authentication process."""
        cookie = request.cookies.get("token")
        if not cookie:
            return None

        token = self.get_token_from_cookie(cookie)

        try:
            payload = jwt.decode(token, constants.SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            raise authentication.AuthenticationError(str(e))

        scopes = ["authenticated"]

        if not payload.get("token"):
            raise authentication.AuthenticationError("Token is missing from JWT.")
        if not payload.get("refresh"):
            raise authentication.AuthenticationError(
                "Refresh token is missing from JWT."
            )

        try:
            user_details = payload.get("user_details")
            if not user_details or not user_details.get("id"):
                raise authentication.AuthenticationError("Improper user details.")
        except Exception:
            raise authentication.AuthenticationError("Could not parse user details.")

        user = User(token, user_details)
        if await user.fetch_admin_status(request):
            scopes.append("admin")

        return authentication.AuthCredentials(scopes), user
