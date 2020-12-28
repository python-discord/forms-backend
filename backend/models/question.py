import typing as t

from pydantic import BaseModel, Field, root_validator, validator

from backend.constants import QUESTION_TYPES, REQUIRED_QUESTION_TYPE_DATA


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
    def validate_question_type(cls, value: str) -> t.Optional[str]:
        """Checks if question type in currently allowed types list."""
        value = value.lower()
        if value not in QUESTION_TYPES:
            raise ValueError(
                f"{value} is not valid question type. "
                f"Allowed question types: {QUESTION_TYPES}."
            )

        return value

    @root_validator
    def validate_question_data(
            cls,
            value: dict[str, t.Any]
    ) -> t.Optional[dict[str, t.Any]]:
        """Check does required data exists for question type and remove other data."""
        # When question type don't need data, don't add anything to keep DB clean.
        if value.get("type") not in REQUIRED_QUESTION_TYPE_DATA:
            return value

        for key, data_type in REQUIRED_QUESTION_TYPE_DATA[value["type"]].items():
            if key not in value.get("data", {}):
                raise ValueError(f"Required question data key '{key}' not provided.")

            if not isinstance(value["data"][key], data_type):
                raise ValueError(
                    f"Question data key '{key}' expects {data_type.__name__}, "
                    f"got {type(value['data'][key]).__name__} instead."
                )

        return value
