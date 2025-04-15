from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, select

from src.api import logger
from src.api.craft.recipes.recipes_schemas import RecipeTable
from src.shared.base import BaseModel, EntityAlreadyExistsError


class RecipeModel(BaseModel[RecipeTable]):
    def __init__(self):
        super().__init__(RecipeTable)

    async def get(
        self,
        session: AsyncSession,
        *,
        element_a_id: int | None = None,
        element_b_id: int | None = None,
        result_id: int | None = None,
    ) -> list[RecipeTable]:
        """Get a recipe by element_a_id, element_b_id, or result_id"""
        # Three params
        if element_b_id and element_a_id and result_id:
            return await self.get_by_other_params(
                session,
                element_a_id=element_a_id,
                element_b_id=element_b_id,
                result_id=result_id,
            )

        # Two params
        elif element_a_id and element_b_id:
            return await self.get_by_other_params(
                session, element_a_id=element_a_id, element_b_id=element_b_id
            )
        elif element_a_id and result_id:
            return await self.get_by_other_params(
                session, element_a_id=element_a_id, result_id=result_id
            )
        elif element_b_id and result_id:
            return await self.get_by_other_params(
                session, element_b_id=element_b_id, result_id=result_id
            )

        # One param
        elif element_a_id:
            return await self.get_by_other_params(session, element_a_id=element_a_id)
        elif element_b_id:
            return await self.get_by_other_params(session, element_b_id=element_b_id)
        elif result_id:
            return await self.get_by_other_params(session, result_id=result_id)

        # No params
        else:
            return await self.get_all(session)

    async def not_exists(
        self, session: AsyncSession, element_a_id: int, element_b_id: int
    ) -> bool:
        query = select(self.model_class).where(
            and_(
                element_a_id == RecipeTable.element_a_id,
                element_b_id == RecipeTable.element_b_id,
            )
        )
        result = await session.execute(query)
        result = list(result.scalars().all())
        try:
            assert len(result) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                entity=element_a_id, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error(f"Error checking if Recipe exists: {e}")
            raise e

        return len(result) == 0

    async def find_recipe_internal(
        self, session: AsyncSession, element_a_id: int, element_b_id: int
    ) -> list[RecipeTable]:
        """Internal helper to find a recipe and its result within a session."""
        stmt = select(RecipeTable).where(
            and_(
                element_a_id == RecipeTable.element_a_id,
                element_b_id == RecipeTable.element_b_id,
            )
        )
        result = await session.execute(stmt)
        return [RecipeTable.model_validate(row) for row in result.scalars().all()]


recipe_model = RecipeModel()
