from dotenv import load_dotenv
load_dotenv()

import os  # noqa
import binascii  # noqa
from enum import Enum  # noqa


FRONTEND_URL = os.getenv("FRONTEND_URL", "https://forms.pythondiscord.com")
DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "pydis_forms")

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.getenv(
    "OAUTH2_REDIRECT_URI",
    "https://forms.pythondiscord.com/callback"
)

GIT_SHA = os.getenv("GIT_SHA", "dev")
FORMS_BACKEND_DSN = os.getenv("FORMS_BACKEND_DSN")

DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(30)).decode())
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD", 267624335836053506)

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


class WebHook(Enum):
    URL = "url"
    MESSAGE = "message"
