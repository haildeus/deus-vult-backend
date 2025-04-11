from sqlmodel import SQLModel

from src.api.craft.elements.elements_schemas import ElementTable  # type: ignore
from src.api.craft.progress.progress_schemas import ProgressTable  # type: ignore
from src.api.craft.recipes.recipes_schemas import RecipeTable  # type: ignore


async def get_craft_registry():
    return SQLModel.metadata
