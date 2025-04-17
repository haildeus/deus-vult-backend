from sqlmodel import MetaData, SQLModel


async def get_craft_registry() -> MetaData:
    return SQLModel.metadata
