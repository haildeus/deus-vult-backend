from enum import Enum


class ReactionEnum(Enum):
    FIRE_REACTION = "🔥"
    FIRE_HEART_REACTION = "❤‍🔥"
    THUMBS_UP_REACTION = "👍"

    THUMBS_DOWN_REACTION = "👎"
    CLOWN_REACTION = "🤡"


REACTION_MESSAGE_MAP = {
    ReactionEnum.FIRE_REACTION: "{user} sent a fire reaction",
    ReactionEnum.FIRE_HEART_REACTION: "{user} sent a fire heart reaction",
    ReactionEnum.THUMBS_UP_REACTION: "{user} sent a thumbs up reaction",
    ReactionEnum.THUMBS_DOWN_REACTION: "{user} sent a thumbs down reaction",
    ReactionEnum.CLOWN_REACTION: "{user} sent a clown reaction",
}
