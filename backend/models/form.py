import typing as t

from pydantic import BaseModel, Field, validator

from backend.constants import FormFeatures
from .question import Question

PUBLIC_FIELDS = ["id", "features", "questions", "name", "description"]


class Form(BaseModel):
    """Schema model for form."""

    id: str = Field(alias="_id")
    features: t.List[str]
    questions: t.List[Question]
    name: str
    description: str

    class Config:
        allow_population_by_field_name = True

    @validator("features")
    def validate_features(cls, value: t.List[str]) -> t.Optional[t.List[str]]:
        """Validates is all features in allowed list."""
        # Uppercase everything to avoid mixed case in DB
        value = [v.upper() for v in value]
        allowed_values = list(v.value for v in FormFeatures.__members__.values())
        if not all(v in allowed_values for v in value):
            raise ValueError("Form features list contains one or more invalid values.")

        if FormFeatures.COLLECT_EMAIL in value and FormFeatures.REQUIRES_LOGIN not in value:  # noqa
            raise ValueError("COLLECT_EMAIL feature require REQUIRES_LOGIN feature.")

        return value

    def dict(self, admin: bool = True, **kwargs: t.Dict) -> t.Dict[str, t.Any]:
        """Wrapper for original function to exclude private data for public access."""
        data = super().dict(**kwargs)
        return {field: data[field] for field in PUBLIC_FIELDS} if admin else data
