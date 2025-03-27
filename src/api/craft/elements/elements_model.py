from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession

from .... import BaseModel
from .elements_schemas import ElementBase, ElementTable


class ElementModel(BaseModel[ElementTable]):
    def __init__(self):
        super().__init__(ElementTable)

    @overload
    async def get(self, session: AsyncSession) -> list[ElementBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, element_id: int
    ) -> list[ElementBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, name: str) -> list[ElementBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        element_id: int | None = None,
        name: str | None = None,
    ) -> list[ElementBase]:
        """Get a user by ID, username, or premium status"""
        if element_id:
            return await self.get_by_id(session, element_id)
        elif name:
            return await self.get_by_other_params(session, name=name)
        else:
            return await self.get_all(session)


element_model = ElementModel()
