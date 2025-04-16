import logging
from typing import cast

from sqlalchemy.exc import SQLAlchemyError

from src.api.craft.recipes.recipes_model import recipe_model
from src.api.craft.recipes.recipes_schemas import CreateRecipe, FetchRecipe, RecipeTable
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.event_registry import RecipeTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.api.craft")


class RecipesService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = recipe_model

    @EventBus.subscribe(RecipeTopics.RECIPE_CREATE)
    @async_traced_function
    async def on_create_recipe(self, event: Event) -> None:
        payload = cast(CreateRecipe, event.extract_payload(event, CreateRecipe))
        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id

        # To satisfy table constraints
        smaller_element_id = min(element_a_id, element_b_id)
        bigger_element_id = max(element_a_id, element_b_id)

        result_id = payload.result_id
        recipe = RecipeTable(
            element_a_id=smaller_element_id,
            element_b_id=bigger_element_id,
            result_id=result_id,
        )
        logger.debug(
            "Creating recipe: %s + %s = %s",
            smaller_element_id,
            bigger_element_id,
            result_id,
        )

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                if await self.model.not_exists(
                    db, smaller_element_id, bigger_element_id
                ):
                    await self.model.add(db, recipe, pass_checks=False)
                else:
                    logger.warning(
                        "Recipe %s + %s = %s already exists, skipping",
                        smaller_element_id,
                        bigger_element_id,
                        result_id,
                    )
                    raise EntityAlreadyExistsError(
                        entity=smaller_element_id, entity_type=RecipeTable.__name__
                    )
            except EntityAlreadyExistsError:
                logger.warning(
                    "Recipe %s + %s = %s already exists, skipping",
                    smaller_element_id,
                    bigger_element_id,
                    result_id,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "SQLAlchemy: %s + %s = %s: %s",
                    smaller_element_id,
                    bigger_element_id,
                    result_id,
                    e,
                )
                raise e
            except Exception as e:
                logger.error(
                    "Error: %s + %s = %s: %s",
                    smaller_element_id,
                    bigger_element_id,
                    result_id,
                    e,
                )
                raise e
        else:
            raise RuntimeError("No active UoW found during recipe creation")

    @EventBus.subscribe(RecipeTopics.RECIPE_FETCH)
    @async_traced_function
    async def on_fetch_recipe(self, event: Event) -> list[RecipeTable]:
        payload = cast(FetchRecipe, event.extract_payload(event, FetchRecipe))

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            recipes = await self.model.get(
                db,
                element_a_id=payload.element_a_id,
                element_b_id=payload.element_b_id,
                result_id=payload.result_id,
            )
            logger.debug("Fetched recipes: %s (length: %s)", recipes, len(recipes))

            return recipes
        else:
            raise RuntimeError("No active UoW found during recipe fetching")
