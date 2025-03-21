from ...core.base import BaseModel
from .session_schemas import GameSession


class GameSessionModel(BaseModel[GameSession]):
    def __init__(self):
        super().__init__(GameSession)


game_session_model = GameSessionModel()
