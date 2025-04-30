import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel, select, tuple_

from src.api.craft.elements.elements_schemas import ElementBase, ElementTable
from src.api.inventory.inventory_exceptions import (
    InventoryNotEnoughItemsException,
)
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

if TYPE_CHECKING:
    from src.api.users.users_schemas import UserTable


class InventoryItemBase(SQLModel):
    # We don't have polymorphic types, so let's use enums at least
    # https://github.com/fastapi/sqlmodel/pull/1226
    class ItemType(enum.StrEnum):
        ELEMENT = enum.auto()
        ITEM = enum.auto()
        MINE = enum.auto()

    inventory_id: int | None = Field(
        foreign_key="inventories.object_id", primary_key=True, index=True
    )

    type: ItemType = Field(primary_key=True)
    sub_type_id: int = Field(default=0, primary_key=True, index=True)

    amount: int = 1
    meta: dict[str, Any] = Field(sa_column=Column(JSONB), default_factory=dict)


class InventoryItemPublic(InventoryItemBase):
    element: ElementBase | None = None


class InventoryItemTable(InventoryItemBase, table=True):
    __tablename__ = "items"

    inventory: "InventoryTable" = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    element: ElementTable | None = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "primaryjoin": "and_(InventoryItemTable.type == 'ELEMENT', foreign(InventoryItemTable.sub_type_id) == ElementTable.object_id)",  # noqa: E501
        },
    )


class InventoryPublic(SQLModel):
    items: list[InventoryItemPublic] = []


class InventoryTable(SQLModel, table=True):
    __tablename__ = "inventories"
    object_id: int = Field(
        default=None,
        primary_key=True,
        index=True,
        unique=True,
        sa_column_kwargs={"autoincrement": True},
    )

    user_id: int = Field(foreign_key="users.object_id", primary_key=True)
    user: "UserTable" = Relationship(
        back_populates="inventory",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    items: list["InventoryItemTable"] = Relationship(
        back_populates="inventory",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @async_traced_function
    async def remove_items(
        self,
        *orders: InventoryItemTable,
    ) -> None:
        items = list(orders)

        uow = current_uow.get()
        session = await uow.get_session()

        stmt = (
            select(InventoryItemTable)
            .where(
                tuple_(  # type: ignore
                    InventoryItemTable.inventory_id,
                    InventoryItemTable.type,
                    InventoryItemTable.sub_type_id,
                ).in_([(self.object_id, item.type, item.sub_type_id) for item in items])
            )
            .with_for_update()
        )

        items_to_remove: list[InventoryItemTable] = list(
            (await session.execute(stmt)).scalars().all()
        )
        if len(items_to_remove) != len(items):
            raise InventoryNotEnoughItemsException("Not enough items.")

        items_to_remove.sort(key=lambda item: (item.type, item.sub_type_id))
        items.sort(key=lambda item: (item.type, item.sub_type_id))

        for item, order in zip(items_to_remove, items, strict=True):
            if item.amount < order.amount:
                raise InventoryNotEnoughItemsException("Not enough items.")

            elif item.amount > order.amount:
                item.amount -= order.amount

            else:
                await session.delete(item)

    @async_traced_function
    async def add_items(self, *orders: InventoryItemTable) -> None:
        uow = current_uow.get()
        session = await uow.get_session()

        for order in orders:
            order.inventory_id = self.object_id

        stmt = (
            select(InventoryItemTable)
            .where(
                tuple_(  # type: ignore
                    InventoryItemTable.inventory_id,
                    InventoryItemTable.type,
                    InventoryItemTable.sub_type_id,
                ).in_(
                    [
                        (item.inventory_id, item.type, item.sub_type_id)
                        for item in orders
                    ]
                )
            )
            .with_for_update()
        )

        fetched_items: list[InventoryItemTable] = list(
            (await session.execute(stmt)).scalars().all()
        )

        existing_items = {
            (item.inventory_id, item.type, item.sub_type_id): item
            for item in fetched_items
        }

        for order in orders:
            if item := existing_items.get(
                (order.inventory_id, order.type, order.sub_type_id)
            ):
                item.amount += order.amount
            else:
                session.add(order)
