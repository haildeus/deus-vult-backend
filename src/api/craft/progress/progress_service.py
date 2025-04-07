from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.progress.progress_model import progress_model
from src.api.craft.progress.progress_schemas import (
    CreateProgress,
    FetchProgress,
    FetchProgressEventResponse,
    ProgressBase,
    ProgressExistsEventResponse,
    ProgressTable,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import ProgressTopics
from src.shared.events import Event
from src.shared.uow import current_uow


class ProgressService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = progress_model

    @EventBus.subscribe(ProgressTopics.PROGRESS_CREATE.value)
    async def on_create_progress(self, event: Event) -> None:
        if not isinstance(event.payload, CreateProgress):
            payload = CreateProgress(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Creating progress: {payload}")

        user_id = payload.user_id
        chat_instance = payload.chat_instance
        element_id = payload.element_id

        progress = ProgressTable(
            object_id=user_id, chat_instance=chat_instance, element_id=element_id
        )

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                await self.model.add(db, progress)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error creating progress: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error creating progress: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during progress creation")

    @EventBus.subscribe(ProgressTopics.PROGRESS_FETCH.value)
    async def on_fetch_progress(self, event: Event) -> FetchProgressEventResponse:
        user_id, chat_instance, element_id = await self.__process_fetch_payload(event)
        try:
            assert user_id or chat_instance
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e

        progress = await self.__fetch_progress(user_id, chat_instance, element_id)
        return FetchProgressEventResponse(progress=progress)

    @EventBus.subscribe(ProgressTopics.PROGRESS_EXISTS.value)
    async def on_progress_exists(self, event: Event) -> ProgressExistsEventResponse:
        user_id, chat_instance, element_id = await self.__process_fetch_payload(event)  # type: ignore
        try:
            assert user_id
            assert chat_instance
            assert element_id
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e

        progress = await self.__fetch_progress(user_id, chat_instance, element_id)
        exists = len(progress) > 0
        return ProgressExistsEventResponse(exists=exists)

    async def __fetch_progress(
        self,
        user_id: int | None,
        chat_instance: int | None,
        element_id: int | None,
    ) -> list[ProgressBase]:
        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                progress = await self.model.get(
                    db,
                    user_id=user_id,
                    chat_instance=chat_instance,
                    element_id=element_id,
                )
                return progress
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error fetching progress: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error fetching progress: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during progress fetching")

    async def __process_fetch_payload(
        self, event: Event
    ) -> tuple[int | None, int | None, int | None]:
        if not isinstance(event.payload, FetchProgress):
            payload = FetchProgress(**event.payload)  # type: ignore
        else:
            payload = event.payload

        user_id = payload.user_id
        chat_instance = payload.chat_instance
        element_id = payload.element_id

        return user_id, chat_instance, element_id
