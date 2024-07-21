"""A submitted response to a form."""

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BigInteger, DateTime, Text

from .base import Base


class FormResponse(Base):
    """A submitted response to a form."""

    __tablename__ = "form_responses"

    response_id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.form_id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(Text)
    user_email: Mapped[str] = mapped_column(Text, nullable=True)
    user_is_admin: Mapped[bool]

    antispam_ip_hash: Mapped[str] = mapped_column(Text, nullable=True)
    antispam_user_agent_hash: Mapped[str] = mapped_column(Text, nullable=True)
    antispam_captcha_pass: Mapped[bool] = mapped_column(nullable=True)
