import jwt
from starlette import authentication
from starlette.requests import Request

from backend import constants, discord

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
            msg = "Unable to split prefix and token from authorization cookie."
            raise authentication.AuthenticationError(msg)

        if prefix.upper() != "JWT":
            msg = f"Invalid authorization cookie prefix '{prefix}'."
            raise authentication.AuthenticationError(msg)

        return token

    async def authenticate(
        self,
        request: Request,
    ) -> tuple[authentication.AuthCredentials, authentication.BaseUser] | None:
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
            msg = "Token is missing from JWT."
            raise authentication.AuthenticationError(msg)
        if not payload.get("refresh"):
            msg = "Refresh token is missing from JWT."
            raise authentication.AuthenticationError(msg)

        try:
            user_details = payload.get("user_details")
            if not user_details or not user_details.get("id"):
                msg = "Improper user details."
                raise authentication.AuthenticationError(msg)  # noqa: TRY301
        except Exception:  # noqa: BLE001
            msg = "Could not parse user details."
            raise authentication.AuthenticationError(msg)

        user = User(
            token,
            user_details,
            await discord.get_member(user_details["id"]),
        )
        if await user.fetch_admin_status(request.state.db):
            scopes.append("admin")

        scopes.extend(await user.get_user_roles(request.state.db))

        return authentication.AuthCredentials(scopes), user
