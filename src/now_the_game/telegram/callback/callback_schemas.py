from enum import Enum

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "telegram.callback"

"""
ENUMS
"""


class CallbackTopics(Enum):
    CALLBACK_QUERY = f"{EVENT_BUS_PREFIX}.query"
    CALLBACK_QUERY_ANSWER = f"{EVENT_BUS_PREFIX}.query.response"


"""
MODELS
"""
