from sqlmodel import MetaData, SQLModel


async def get_telegram_registry() -> MetaData:
    return SQLModel.metadata
