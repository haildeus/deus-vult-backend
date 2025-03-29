from enum import Enum

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "telegram.inline"

"""
ENUMS
"""


class CallbackTopics(Enum):
    INLINE_QUERY = f"{EVENT_BUS_PREFIX}.query"
    INLINE_QUERY_RESULT = f"{EVENT_BUS_PREFIX}.query.response"


"""
MODELS
"""
