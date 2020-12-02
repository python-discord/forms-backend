import typing as t

from pydantic import BaseModel, Field, validator

from backend.constants import QUESTION_TYPES, REQUIRED_QUESTION_TYPE_DATA


class Question(BaseModel):
    """Schema model for form question."""

    id: str = Field(alias="_id")
    name: str
    type: str
    data: t.Dict[str, t.Any]

    @validator("type", pre=True)
    def validate_question_type(cls, value: str) -> t.Optional[str]:
        """Checks if question type in currently allowed types list."""
        value = value.lower()
        if value not in QUESTION_TYPES:
            raise ValueError(
                f"{value} is not valid question type. "
                f"Allowed question types: {QUESTION_TYPES}."
            )

        return value

    @validator("data")
    def validate_question_data(
            cls,
            value: t.Dict[str, t.Any]
    ) -> t.Optional[t.Dict[str, t.Any]]:
        """Check does required data exists for question type and remove other data."""
        # When question type don't need data, don't add anything to keep DB clean.
        if cls.type not in REQUIRED_QUESTION_TYPE_DATA:
            return {}

        # Required keys (and values) will be stored to here
        # to remove all unnecessary stuff
        result = {}

        for key, data_type in REQUIRED_QUESTION_TYPE_DATA[cls.type].items():
            if key not in value:
                raise ValueError(f"Required question data key '{key}' not provided.")

            if not isinstance(value[key], data_type):
                raise ValueError(
                    f"Question data key '{key}' expects {data_type.__name__}, "
                    f"got {type(value[key]).__name__} instead."
                )

            result[key] = value[key]

        return result
