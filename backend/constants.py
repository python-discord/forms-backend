import binascii
import os
from enum import Enum

from dotenv import load_dotenv
from redis.asyncio import Redis as _Redis

load_dotenv()


FRONTEND_URL = os.getenv("FRONTEND_URL", "https://forms.pythondiscord.com")
DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "pydis_forms")
SNEKBOX_URL = os.getenv("SNEKBOX_URL", "http://snekbox.default.svc.cluster.local/eval")

REDIS_CLIENT = _Redis.from_url(os.getenv("REDIS_URL"), encoding="utf-8")

PRODUCTION = os.getenv("PRODUCTION", "True").lower() != "false"
PRODUCTION_URL = "https://forms.pythondiscord.com"

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.getenv(
    "OAUTH2_REDIRECT_URI",
    "https://forms.pythondiscord.com/callback",
)

GIT_SHA = os.getenv("GIT_SHA", "dev")
FORMS_BACKEND_DSN = os.getenv("FORMS_BACKEND_DSN")

DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(30)).decode())
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD", "267624335836053506")

HCAPTCHA_API_SECRET = os.getenv("HCAPTCHA_API_SECRET")

QUESTION_TYPES = [
    "radio",
    "checkbox",
    "select",
    "short_text",
    "textarea",
    "code",
    "range",
    "section",
    "timezone",
    "vote",
]

REQUIRED_QUESTION_TYPE_DATA = {
    "radio": {
        "options": list,
    },
    "select": {
        "options": list,
    },
    "code": {
        "language": str,
    },
    "range": {
        "options": list,
    },
    "section": {
        "text": str,
    },
    "vote": {
        "options": list,
    },
}

DISCORD_API_BASE_URL = "https://discord.com/api/v8"


class FormFeatures(Enum):
    """Lists form features. Read more in SCHEMA.md."""

    DISCOVERABLE = "DISCOVERABLE"
    REQUIRES_LOGIN = "REQUIRES_LOGIN"
    OPEN = "OPEN"
    COLLECT_EMAIL = "COLLECT_EMAIL"
    DISABLE_ANTISPAM = "DISABLE_ANTISPAM"
    WEBHOOK_ENABLED = "WEBHOOK_ENABLED"
    ASSIGN_ROLE = "ASSIGN_ROLE"
    UNIQUE_RESPONDER = "UNIQUE_RESPONDER"


class WebHook(Enum):
    URL = "url"
    MESSAGE = "message"
