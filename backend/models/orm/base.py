"""The base classes for ORM models."""

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import MetaData

NAMING_CONVENTIONS = {
    "ix": "%(column_0_label)s_ix",
    "uq": "%(table_name)s_%(column_0_name)s_uq",
    "ck": "%(table_name)s_%(constraint_name)s_ck",
    "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fk",
    "pk": "%(table_name)s_pk",
}


class Base(AsyncAttrs, DeclarativeBase):
    """Classes that inherit this class will be automatically mapped using declarative mapping."""

    metadata = MetaData(naming_convention=NAMING_CONVENTIONS)

    def patch_from_pydantic(self, pydantic_model: BaseModel) -> None:
        """Patch this model using the given pydantic model, unspecified attributes remain the same."""
        for key, value in pydantic_model.dict(exclude_unset=True).items():
            setattr(self, key, value)
