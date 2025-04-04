from sqlmodel import Relationship, SQLModel

from src.api.craft.elements.elements_schemas import ElementTable
from src.api.craft.recipes.recipes_schemas import RecipeTable

"""
ELEMENT RELATIONSHIPS
"""

ElementTable.recipes_as_a = Relationship(
    back_populates="element_a",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.element_a_id]",
    },
)
ElementTable.recipes_as_b = Relationship(
    back_populates="element_b",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.element_b_id]",
    },
)
ElementTable.recipes_as_result = Relationship(
    back_populates="result",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.result_id]",
    },
)

"""
RECIPE RELATIONSHIPS
"""

RecipeTable.element_a = Relationship(
    back_populates="recipes_as_a",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.element_a_id]",
    },
)
RecipeTable.element_b = Relationship(
    back_populates="recipes_as_b",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.element_b_id]",
    },
)
RecipeTable.result = Relationship(
    back_populates="recipes_as_result",
    sa_relationship_kwargs={
        "lazy": "selectin",
        "foreign_keys": "[RecipeTable.result_id]",
    },
)


async def get_craft_registry():
    return SQLModel.metadata
