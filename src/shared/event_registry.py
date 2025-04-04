from enum import Enum

"""
EVENT BUS TOPICS CONSTANTS
"""

FETCH_PREFIX = "fetch"
CREATE_PREFIX = "create"
UPDATE_PREFIX = "update"
DELETE_PREFIX = "delete"
RESPONSE_PREFIX = "response"
QUERY_PREFIX = "query"

CRUD_OPERATIONS = (
    ("CREATE", CREATE_PREFIX),
    ("FETCH", FETCH_PREFIX),
    ("UPDATE", UPDATE_PREFIX),
    ("DELETE", DELETE_PREFIX),
)


"""
API
"""
API_PREFIX = "api"
CRAFT_PREFIX = f"{API_PREFIX}.craft"
CRAFT_ELEMENTS_PREFIX = f"{CRAFT_PREFIX}.elements"
CRAFT_RECIPES_PREFIX = f"{CRAFT_PREFIX}.recipes"


class ElementTopics(Enum):
    ELEMENT_CREATE = f"{CRAFT_ELEMENTS_PREFIX}.{CREATE_PREFIX}"
    ELEMENT_FETCH = f"{CRAFT_ELEMENTS_PREFIX}.{FETCH_PREFIX}"
    ELEMENT_FETCH_RESPONSE = f"{CRAFT_ELEMENTS_PREFIX}.{FETCH_PREFIX}.{RESPONSE_PREFIX}"
    ELEMENT_COMBINATION = f"{CRAFT_ELEMENTS_PREFIX}.combination.{QUERY_PREFIX}"
    ELEMENT_COMBINATION_RESPONSE = (
        f"{CRAFT_ELEMENTS_PREFIX}.combination.{RESPONSE_PREFIX}"
    )


class RecipeTopics(Enum):
    RECIPE_CREATE = f"{CRAFT_RECIPES_PREFIX}.{CREATE_PREFIX}"
    RECIPE_FETCH = f"{CRAFT_RECIPES_PREFIX}.{FETCH_PREFIX}"
    RECIPE_FETCH_RESPONSE = f"{CRAFT_RECIPES_PREFIX}.{FETCH_PREFIX}.{RESPONSE_PREFIX}"


"""
TELEGRAM
"""
TELEGRAM_PREFIX = "telegram"
TELEGRAM_CALLBACK_PREFIX = f"{TELEGRAM_PREFIX}.callback"
TELEGRAM_CHAT_PREFIX = f"{TELEGRAM_PREFIX}.chats"
TELEGRAM_INLINE_PREFIX = f"{TELEGRAM_PREFIX}.inline"
TELEGRAM_MEMBERSHIP_PREFIX = f"{TELEGRAM_PREFIX}.memberships"
TELEGRAM_MESSAGE_PREFIX = f"{TELEGRAM_PREFIX}.messages"
TELEGRAM_POLL_PREFIX = f"{TELEGRAM_PREFIX}.polls"
TELEGRAM_USER_PREFIX = f"{TELEGRAM_PREFIX}.users"


class CallbackTopics(Enum):
    CALLBACK_GAME_UPDATE = f"{TELEGRAM_CALLBACK_PREFIX}.game.update"


class ChatTopics(Enum):
    CHAT_CREATE = f"{TELEGRAM_CHAT_PREFIX}.{CREATE_PREFIX}"


class MembershipTopics(Enum):
    MEMBERSHIP_CREATE = f"{TELEGRAM_MEMBERSHIP_PREFIX}.{CREATE_PREFIX}"
    MEMBERSHIP_UPDATE = f"{TELEGRAM_MEMBERSHIP_PREFIX}.{UPDATE_PREFIX}"


class MessageTopics(Enum):
    MESSAGE_CREATE = f"{TELEGRAM_MESSAGE_PREFIX}.{CREATE_PREFIX}"


class PollTopics(Enum):
    POLL_CREATE = f"{TELEGRAM_POLL_PREFIX}.{CREATE_PREFIX}"
    POLL_SEND = f"{TELEGRAM_POLL_PREFIX}.send"


class UserTopics(Enum):
    USER_CREATE = f"{TELEGRAM_USER_PREFIX}.{CREATE_PREFIX}"


"""
AGENTS
"""
AGENTS_PREFIX = "agents"
AGENTS_GLIF_PREFIX = f"{AGENTS_PREFIX}.glif"
AGENTS_LANGUAGE_MODEL_PREFIX = f"{AGENTS_PREFIX}.language_model"
AGENTS_LANGUAGE_MODEL_TEXT_PREFIX = f"{AGENTS_LANGUAGE_MODEL_PREFIX}.text"
AGENTS_LANGUAGE_MODEL_MULTIMODAL_PREFIX = f"{AGENTS_LANGUAGE_MODEL_PREFIX}.multimodal"


class LanguageModelTopics(Enum):
    TEXT_QUERY = f"{AGENTS_LANGUAGE_MODEL_TEXT_PREFIX}.{QUERY_PREFIX}"
    TEXT_RESPONSE = f"{AGENTS_LANGUAGE_MODEL_TEXT_PREFIX}.{RESPONSE_PREFIX}"
    MULTI_MODAL_QUERY = f"{AGENTS_LANGUAGE_MODEL_MULTIMODAL_PREFIX}.{QUERY_PREFIX}"
    MULTI_MODAL_RESPONSE = (
        f"{AGENTS_LANGUAGE_MODEL_MULTIMODAL_PREFIX}.{RESPONSE_PREFIX}"
    )


class GlifTopics(Enum):
    QUERY = f"{AGENTS_GLIF_PREFIX}.{QUERY_PREFIX}"
    RESPONSE = f"{AGENTS_GLIF_PREFIX}.{RESPONSE_PREFIX}"
