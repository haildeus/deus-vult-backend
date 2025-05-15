import logging

from pyrogram.client import Client
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.message_reaction_handler import MessageReactionHandler
from pyrogram.types import MessageReactionUpdated

from src.now_the_game.telegram.reactions.reactions_constants import (
    REACTION_MESSAGE_MAP,
    ReactionEnum,
)
from src.now_the_game.telegram.reactions.reactions_utils import (
    is_custom_emoji,
    isolate_new_reaction,
)

logger = logging.getLogger("deus-vult.telegram.reactions")


class ReactionsHandlers:
    """
    Reactions handlers class
    """

    @staticmethod
    async def on_reaction_update(
        client: Client, message_reaction_updated: MessageReactionUpdated
    ) -> None:
        new_reactions = message_reaction_updated.new_reaction
        old_reactions = message_reaction_updated.old_reaction

        reaction_change = isolate_new_reaction(old_reactions, new_reactions)
        if reaction_change is None:
            pass
        else:
            if is_custom_emoji(reaction_change):
                pass
            else:
                try:
                    reaction_enum = ReactionEnum(reaction_change.emoji)
                    reaction_message = REACTION_MESSAGE_MAP[reaction_enum]

                    # Send notification
                    await client.send_message(
                        chat_id=message_reaction_updated.chat.id,
                        text=reaction_message.format(
                            user=message_reaction_updated.user.first_name
                        ),
                    )
                except ValueError:
                    pass
                except Exception as e:
                    raise e

    @property
    def reactions_handlers(self) -> list[Handler]:
        return [
            MessageReactionHandler(
                ReactionsHandlers.on_reaction_update,
            ),
        ]
