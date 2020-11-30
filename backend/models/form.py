import typing as t

from pydantic import BaseModel, Field, validator

from backend.constants import FormFeatures
from backend.models import Question
from backend.models.types import ObjectId


class Form(BaseModel):
    """Schema model for form."""

    id: ObjectId = Field(alias="_id")
    features: t.List[str]
    questions: t.List[Question]

    @validator("features")
    def validate_features(self, value: t.List[str]) -> t.Optional[t.List[str]]:
        """Validates is all features in allowed list."""
        # Uppercase everything to avoid mixed case in DB
        value = [v.upper() for v in value]
        if not all(v in FormFeatures.__members__.values() for v in value):
            raise ValueError("Form features list contains one or more invalid values.")

        return value
