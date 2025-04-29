from sqlmodel import Field

from src.shared.base import BaseSchema

"""
MODELS
"""


class ProgressTable(BaseSchema, table=True):
    __tablename__ = "progress"  # type: ignore

    recipe_id: int = Field(
        primary_key=True,
        foreign_key="recipes.object_id",
        index=True,
    )
