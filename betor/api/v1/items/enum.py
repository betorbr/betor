import enum


class ItemsSortEnum(enum.StrEnum):
    inserted_at_asc = "inserted_at"
    inserted_at_desc = "-inserted_at"
    updated_at_asc = "updated_at"
    updated_at_desc = "-updated_at"
