from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship

from ...core.base import BaseSchema

from ..telegram_schemas import PollSchema, PollOptionSchema
