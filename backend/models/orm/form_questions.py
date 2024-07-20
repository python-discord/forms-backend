"""Discord members who have admin access."""

from typing import ClassVar

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.constants import TextType

from .base import Base


class FormQuestion(Base):
    __tablename__ = "form_questions"

    question_id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.form_id"))
    name: Mapped[str]
    type: Mapped[str]
    required: Mapped[bool]

    __mapper_args__: ClassVar = {"polymorphic_identity": "form_questions", "polymorphic_on": "type"}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class QuestionWithOptions:
    options: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        use_existing_column=True,
    )


class FormRadioQuestion(QuestionWithOptions, FormQuestion):
    """A radio question type."""

    __tablename__ = "form_radio_questions"

    radio_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_radio_questions",
    }


class FormCheckboxQuestion(QuestionWithOptions, FormQuestion):
    """A radio question type."""

    __tablename__ = "form_checkbox_questions"

    checkbox_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_checkbox_questions",
    }


class FormRangeQuestion(QuestionWithOptions, FormQuestion):
    """A range question type."""

    __tablename__ = "form_range_questions"

    range_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_range_questions",
    }


class FormVoteQuestion(QuestionWithOptions, FormQuestion):
    """A vote question type."""

    __tablename__ = "form_vote_questions"

    range_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_vote_questions",
    }


class FormSelectQuestion(QuestionWithOptions, FormQuestion):
    """A select question type."""

    __tablename__ = "form_select_questions"

    select_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_select_questions",
    }


class FormTextQuestion(FormQuestion):
    """A text question type."""

    __tablename__ = "form_text_questions"

    text_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )
    text_type: Mapped[TextType] = mapped_column(Enum(TextType))

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_text_questions",
    }


class FormCodeQuestion(FormQuestion):
    """A code question type."""

    __tablename__ = "form_code_questions"

    code_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )
    language: Mapped[str]
    allow_failure: Mapped[bool]
    unit_tests: Mapped[list["FormCodeQuestionTest"]] = relationship(
        cascade="all, delete",
        passive_deletes=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_code_questions",
    }


class FormCodeQuestionTest(Base):
    """Unit tests for a given code question."""

    __tablename__ = "form_code_question_tests"
    test_id: Mapped[int] = mapped_column(primary_key=True)
    code_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_code_questions.code_question_id")
    )
    name: Mapped[str]
    code: Mapped[str]


class FormSectionQuestion(FormQuestion):
    """A section question type."""

    __tablename__ = "form_section_questions"

    section_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )
    text: Mapped[str]

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_section_questions",
    }


class FormTimezoneQuestion(FormQuestion):
    """A timezone question type."""

    __tablename__ = "form_timezone_questions"

    timezone_question_id: Mapped[int] = mapped_column(
        ForeignKey("form_questions.question_id"),
        primary_key=True,
    )

    __mapper_args__: ClassVar = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "form_timezone_questions",
    }
