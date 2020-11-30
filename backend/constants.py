from dotenv import load_dotenv
load_dotenv()

import os  # noqa
import binascii  # noqa

DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "pydis_forms")

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.getenv(
    "OAUTH2_REDIRECT_URI",
    "http://forms.pythondiscord.com/callback"
)

SECRET_KEY = os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(30)).decode())

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
