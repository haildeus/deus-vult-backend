import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.now_the_game.game.clans.clans_schemas import ClanTable
from src.shared.base import BaseModel, EntityAlreadyExistsError

logger = logging.getLogger("deus-vult.clans_model")


class ClanModel(BaseModel[ClanTable]):
    def __init__(self) -> None:
        super().__init__(ClanTable)

    async def get(
        self,
        session: AsyncSession,
        *,
        chat_id: int | None = None,
        chat_instance: int | None = None,
    ) -> list[ClanTable]:
        if chat_id and chat_instance:
            logger.error(
                "chat_id and chat_instance cannot both be provided: %s, %s",
                chat_id,
                chat_instance,
            )
            raise ValueError("chat_id and chat_instance cannot both be provided")

        elif chat_id:
            logger.debug("From chat %s fetching all clans", chat_id)
            return await self.get_by_other_params(session, chat_id=chat_id)
        elif chat_instance:
            logger.debug("From chat instance %s fetching all clans", chat_instance)
            return await self.get_by_other_params(session, chat_instance=chat_instance)
        else:
            logger.debug("Fetching all clans")
            return await self.get_all(session)

    async def not_exists(
        self,
        session: AsyncSession,
        chat_id: int | None = None,
        chat_instance: int | None = None,
    ) -> bool:
        fetched_clans = await self.get(
            session, chat_id=chat_id, chat_instance=chat_instance
        )
        try:
            assert len(fetched_clans) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                chat_id, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error("Error checking if clan exists: %s", e)
            raise e

        return True


clan_model = ClanModel()
