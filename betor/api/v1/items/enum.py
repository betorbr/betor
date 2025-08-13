import enum

from betor.repositories import ItemsRepository


class ItemsSortEnum(enum.StrEnum):
    inserted_at_asc = ItemsRepository.INSERTED_AT_FIELD
    inserted_at_desc = f"-{ItemsRepository.INSERTED_AT_FIELD}"
    updated_at_asc = ItemsRepository.UPDATED_AT_FIELD
    updated_at_desc = f"-{ItemsRepository.UPDATED_AT_FIELD}"
