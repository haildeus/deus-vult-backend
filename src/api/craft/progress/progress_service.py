from typing import cast

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.progress.progress_model import progress_model
from src.api.craft.progress.progress_schemas import (
    CheckProgress,
    FetchProgress,
    InitProgress,
    Progress,
    ProgressBase,
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
    
    @EventBus.subscribe(ProgressTopics.PROGRESS_INIT)
    async def on_init_progress(self, event: Event) -> None:
        payload = cast(InitProgress, event.extract_payload(event, InitProgress))
        user_id = payload.user_id
        chat_instance = payload.chat_instance
        starting_elements_ids = payload.starting_elements_ids
        
        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            for element_id in starting_elements_ids:
                print(f"Adding progress for user {user_id} with element {element_id}")
                progress = ProgressTable(
                    object_id=user_id, chat_instance=chat_instance, element_id=element_id
                )
                print(f"Progress: {progress}")
                await self.model.add(db, progress, pass_checks=False)
        else:
            raise RuntimeError("No active UoW found during progress initialization")

    @EventBus.subscribe(ProgressTopics.PROGRESS_CREATE)
    async def on_create_progress(self, event: Event) -> list[ProgressTable]:
        payload = cast(Progress, event.extract_payload(event, Progress))
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
                response = await self.model.add(db, progress)
                return response
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error creating progress: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error creating progress: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during progress creation")

    @EventBus.subscribe(ProgressTopics.PROGRESS_FETCH)
    async def on_fetch_progress(self, event: Event) -> list[ProgressBase]:
        user_id, chat_instance, element_id = await self.__process_fetch_payload(event)
        try:
            assert user_id or chat_instance
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e

        progress = await self.__fetch_progress(user_id, chat_instance, element_id)
        return progress

    @EventBus.subscribe(ProgressTopics.PROGRESS_CHECK)
    async def on_check_progress(self, event: Event) -> None:
        payload = cast(CheckProgress, event.extract_payload(event, CheckProgress))

        user_id = payload.user_id
        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            exists = await self.model.check_access_internal(
                db, user_id, element_a_id, element_b_id
            )
        else:
            raise RuntimeError("No active UoW found during progress checking")

        if not exists:
            logger.error(
                f"User {user_id} does not have access "
                f"to element {element_a_id} or {element_b_id}"
            )
            raise HTTPException(
                status_code=400,
                detail="You don't have access to one or both input elements",
            )
        else:
            logger.debug(
                f"User {user_id} has access to {element_a_id} and {element_b_id}"
            )

    @EventBus.subscribe(ProgressTopics.PROGRESS_EXISTS)
    async def on_progress_exists(self, event: Event) -> bool:
        user_id, chat_instance, element_id = await self.__process_fetch_payload(event)  # type: ignore
        try:
            assert user_id
            assert chat_instance
            assert element_id
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e

        progress = await self.__fetch_progress(user_id, chat_instance, element_id)
        exists = len(progress) > 0
        return exists

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
