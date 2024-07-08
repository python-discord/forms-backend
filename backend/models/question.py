import typing as t

from pydantic import BaseModel, Field, root_validator, validator

from backend.constants import QUESTION_TYPES, REQUIRED_QUESTION_TYPE_DATA

_TESTS_TYPE = dict[str, str] | int


class Unittests(BaseModel):
    """Schema model for unittest suites in code questions."""

    allow_failure: bool = False
    tests: _TESTS_TYPE

    @validator("tests")
    def validate_tests(cls, value: _TESTS_TYPE) -> _TESTS_TYPE:
        """Confirm that at least one test exists in a test suite."""
        if isinstance(value, dict):
            keys = len(value.keys()) - (1 if "setUp" in value else 0)
            if keys == 0:
                msg = "Must have at least one test in a test suite."
                raise ValueError(msg)

        return value


class CodeQuestion(BaseModel):
    """Schema model for questions of type `code`."""

    language: str
    unittests: Unittests | None


class Question(BaseModel):
    """Schema model for form question."""

    id: str = Field(alias="_id")
    name: str
    type: str
    data: dict[str, t.Any]
    required: bool

    class Config:
        allow_population_by_field_name = True

    @validator("type", pre=True)
    def validate_question_type(cls, value: str) -> str:
        """Checks if question type in currently allowed types list."""
        value = value.lower()
        if value not in QUESTION_TYPES:
            msg = f"{value} is not valid question type. Allowed question types: {QUESTION_TYPES}."
            raise ValueError(msg)

        return value

    @root_validator
    def validate_question_data(
        cls,
        value: dict[str, t.Any],
    ) -> dict[str, t.Any]:
        """Check does required data exists for question type and remove other data."""
        # When question type don't need data, don't add anything to keep DB clean.
        if value.get("type") not in REQUIRED_QUESTION_TYPE_DATA:
            return value

        for key, data_type in REQUIRED_QUESTION_TYPE_DATA[value["type"]].items():
            if key not in value.get("data", {}):
                msg = f"Required question data key '{key}' not provided."
                raise ValueError(msg)

            if not isinstance(value["data"][key], data_type):
                msg = (
                    f"Question data key '{key}' expects {data_type.__name__}, "
                    f"got {type(value["data"][key]).__name__} instead."
                )
                raise TypeError(msg)

            # Validate unittest options
            if value.get("type").lower() == "code":
                value["data"] = CodeQuestion(**value.get("data")).dict()

        return value
