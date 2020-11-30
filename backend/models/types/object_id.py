import typing as t
from bson import ObjectId as OriginalObjectId


class ObjectId(OriginalObjectId):
    """ObjectId implementation for Pydantic."""

    @classmethod
    def __get_validators__(cls) -> t.Generator[t.Callable, None, None]:
        """Get validators for Pydantic."""
        yield cls.validate

    @classmethod
    def validate(cls, value: t.Any) -> t.Optional["ObjectId"]:
        """Checks value validity to become ObjectId and if valid, return ObjectId."""
        if OriginalObjectId.is_valid(value):
            raise ValueError(f"Invalid value '{value}' for ObjectId.")
        return ObjectId(value)

    @classmethod
    def __modify_schema__(cls, field_schema: t.Dict[str, t.Any]) -> None:
        """Update data type to string."""
        field_schema.update(type="string")
