from sqlmodel import MetaData, SQLModel

from src.now_the_game.game.characters.characters_schemas import CharacterTable
from src.now_the_game.game.clans.clans_schemas import ClanTable


async def get_game_registry() -> MetaData:
    return SQLModel.metadata
