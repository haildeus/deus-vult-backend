import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.now_the_game.game.characters.characters_schemas import CharacterTable
from src.shared.base import BaseModel, EntityAlreadyExistsError

logger = logging.getLogger("deus-vult.characters_model")


class CharacterModel(BaseModel[CharacterTable]):
    def __init__(self) -> None:
        super().__init__(CharacterTable)

    async def get(
        self,
        session: AsyncSession,
        *,
        user_id: int | None = None,
        clan_id: int | None = None,
    ) -> list[CharacterTable]:
        if user_id and clan_id:
            logger.debug(
                "From clan %s fetching character of user %s",
                clan_id,
                user_id,
            )
            return await self.get_by_other_params(
                session, user_id=user_id, clan_id=clan_id
            )
        elif user_id:
            logger.debug("From user %s fetching all characters", user_id)
            return await self.get_by_other_params(session, user_id=user_id)
        elif clan_id:
            logger.debug("From clan %s fetching all characters", clan_id)
            return await self.get_by_other_params(session, clan_id=clan_id)
        else:
            logger.debug("Fetching all characters")
            return await self.get_all(session)

    async def not_exists(
        self,
        session: AsyncSession,
        user_id: int | None = None,
        clan_id: int | None = None,
    ) -> bool:
        fetched_characters = await self.get(session, user_id=user_id, clan_id=clan_id)
        try:
            assert len(fetched_characters) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                user_id, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error("Error checking if character exists: %s", e)
            raise e

        return True


character_model = CharacterModel()
