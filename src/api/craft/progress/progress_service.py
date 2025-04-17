import logging
from typing import cast

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.api.craft.progress.progress_model import progress_model
from src.api.craft.progress.progress_schemas import (
    CheckProgress,
    FetchProgress,
    InitProgress,
    Progress,
    ProgressTable,
)
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.event_registry import ProgressTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.api.craft")


class ProgressService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self.model = progress_model

    @EventBus.subscribe(ProgressTopics.PROGRESS_INIT)
    @async_traced_function
    async def on_init_progress(self, event: Event) -> None:
        payload = cast(InitProgress, event.extract_payload(event, InitProgress))
        user_id = payload.user_id
        chat_instance = payload.chat_instance
        starting_elements_ids = payload.starting_elements_ids

        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            for element_id in starting_elements_ids:
                progress = ProgressTable(
                    object_id=user_id,
                    chat_instance=chat_instance,
                    element_id=element_id,
                )
                await self.model.add(db, progress, pass_checks=False)
        else:
            raise RuntimeError("No active UoW found during progress initialization")

    @EventBus.subscribe(ProgressTopics.PROGRESS_CREATE)
    @async_traced_function
    async def on_create_progress(self, event: Event) -> list[ProgressTable]:
        payload = cast(Progress, event.extract_payload(event, Progress))
        logger.debug("Creating progress: %s", payload)
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
                not_exists = await self.model.not_exists(db, user_id, element_id)
                # If the progress does not exist, create it
                if not_exists:
                    logger.debug(
                        "Element %s does not exist for user %s, creating progress",
                        element_id,
                        user_id,
                    )
                    response = await self.model.add(db, progress, pass_checks=False)
                    return response

                # If the progress exists, return the progress
                else:
                    logger.debug(
                        "Element %s already exists for user %s, returning progress",
                        element_id,
                        user_id,
                    )
                    return [progress]

            except EntityAlreadyExistsError:
                logger.warning(
                    "Element %s already exists for user %s, returning progress",
                    element_id,
                    user_id,
                )
                return [progress]
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy error creating progress: %s", e)
                raise e
            except Exception as e:
                logger.error("Error creating progress: %s", e)
                raise e
        else:
            raise RuntimeError("No active UoW found during progress creation")

    @EventBus.subscribe(ProgressTopics.PROGRESS_FETCH)
    @async_traced_function
    async def on_fetch_progress(self, event: Event) -> list[ProgressTable]:
        payload = cast(FetchProgress, event.extract_payload(event, FetchProgress))
        user_id = payload.user_id
        chat_instance = payload.chat_instance
        element_id = payload.element_id

        try:
            assert user_id or chat_instance
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e

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
                logger.error("SQLAlchemy error fetching progress: %s", e)
                raise e
            except Exception as e:
                logger.error("Error fetching progress: %s", e)
                raise e
        else:
            raise RuntimeError("No active UoW found during progress fetching")

    @EventBus.subscribe(ProgressTopics.PROGRESS_CHECK)
    @async_traced_function
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
                "User %s does not have access to element %s or %s",
                user_id,
                element_a_id,
                element_b_id,
            )
            raise HTTPException(
                status_code=400,
                detail="You don't have access to one or both input elements",
            )
        else:
            logger.debug(
                "User %s has access to %s and %s",
                user_id,
                element_a_id,
                element_b_id,
            )

    @EventBus.subscribe(ProgressTopics.PROGRESS_EXISTS)
    @async_traced_function
    async def on_progress_exists(self, event: Event) -> bool:
        user_id, chat_instance, element_id = await self.__process_fetch_payload(event)
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
    ) -> list[ProgressTable]:
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
                logger.error("SQLAlchemy error fetching progress: %s", e)
                raise e
            except Exception as e:
                logger.error("Error fetching progress: %s", e)
                raise e
        else:
            raise RuntimeError("No active UoW found during progress fetching")

    @staticmethod
    async def __process_fetch_payload(
        event: Event
    ) -> tuple[int | None, int | None, int | None]:
        if not isinstance(event.payload, FetchProgress):
            payload = FetchProgress(**event.payload)  # type: ignore
        else:
            payload = event.payload

        user_id = payload.user_id
        chat_instance = payload.chat_instance
        element_id = payload.element_id

        return user_id, chat_instance, element_id
