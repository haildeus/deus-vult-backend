from pyrogram.types import Reaction


def isolate_new_reaction(
    old_reactions: list[Reaction], new_reactions: list[Reaction]
) -> Reaction | None:
    if len(new_reactions) == 0 or len(old_reactions) > len(new_reactions):
        return None

    # Take the unique value from the new reactions without using set()
    new_reaction = [
        reaction for reaction in new_reactions if reaction not in old_reactions
    ]
    return new_reaction[0]


def is_custom_emoji(reaction: Reaction) -> bool:
    return reaction.custom_emoji_id is not None
