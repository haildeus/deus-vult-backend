from ...core.base import BaseModel
from .characters_schemas import Character, Lore, PrimaryStats


class CharacterModel(BaseModel[Character]):
    def __init__(self):
        super().__init__(Character)


class LoreModel(BaseModel[Lore]):
    def __init__(self):
        super().__init__(Lore)


class PrimaryStatsModel(BaseModel[PrimaryStats]):
    def __init__(self):
        super().__init__(PrimaryStats)


character_model = CharacterModel()
lore_model = LoreModel()
primary_stats_model = PrimaryStatsModel()
