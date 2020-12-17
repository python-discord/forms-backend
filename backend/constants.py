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

DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(30)).decode())

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


class FormFeatures(Enum):
    """Lists form features. Read more in SCHEMA.md."""

    DISCOVERABLE = "DISCOVERABLE"
    REQUIRES_LOGIN = "REQUIRES_LOGIN"
    OPEN = "OPEN"
    COLLECT_EMAIL = "COLLECT_EMAIL"
    DISABLE_ANTISPAM = "DISABLE_ANTISPAM"
    WEBHOOK_ENABLED = "WEBHOOK_ENABLED"
