"""All forms that can have submissions."""

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import BigInteger, Enum, Text

from backend.constants import FormFeatures

from .base import Base


class Form(Base):
    """A form that users can submit responses to."""

    __tablename__ = "forms"

    form_id: Mapped[int] = mapped_column(primary_key=True)

    short_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    submission_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    discord_role: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    features: Mapped[list[FormFeatures]] = mapped_column(pg.ARRAY(Enum(FormFeatures), dimensions=1))

    form_response_readers: Mapped[list["FormResponseReader"]] = relationship(
        cascade="all, delete",
        passive_deletes=True,
    )
    form_editors: Mapped[list["FormEditor"]] = relationship(
        cascade="all, delete",
        passive_deletes=True,
    )


class FormResponseReader(Base):
    """A Discord user that can read a given form."""

    __tablename__ = "form_response_readers"

    form_id: Mapped[int] = mapped_column(
        ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class FormEditor(Base):
    """A Discord user that can edit a given form."""

    __tablename__ = "form_editors"

    form_id: Mapped[int] = mapped_column(
        ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
