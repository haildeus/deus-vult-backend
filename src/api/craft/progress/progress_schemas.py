from sqlmodel import Field, Relationship

from src.api.craft.recipes.recipes_schemas import RecipeTable
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

    recipe: RecipeTable = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
        }
    )
