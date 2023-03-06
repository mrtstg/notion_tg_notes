import enum
from typing import Any


class NotionDatabasePropertyEnum(enum.Enum):
    (
        CHECKBOX,
        CREATED_BY,
        CREATED_TIME,
        DATE,
        EMAIL,
        FILES,
        FORMULA,
        LAST_EDITED_BY,
        LAST_EDITED_TIME,
        MULTI_SELECT,
        NUMBER,
        PEOPLE,
        PHONE_NUMBER,
        RELATION,
        RICH_TEXT,
        ROLLUP,
        SELECT,
        STATUS,
        TITLE,
        URL,
    ) = range(20)

    @staticmethod
    def from_string(value: str) -> int:
        return getattr(NotionDatabasePropertyEnum, value.upper())

    @staticmethod
    def to_string(value: int) -> int:
        return value.name.lower()  # type: ignore


class NotionDatabaseProperty:
    id: str
    name: str
    type: NotionDatabasePropertyEnum | Any

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.type = NotionDatabasePropertyEnum.from_string(data["type"])

    def __repr__(self) -> str:
        return "<DbProperty: %s %s>" % (self.name, self.type.name)


class NotionDatabase:
    _data: dict
    id: str

    def __init__(self, data: dict):
        self._data = data
        self.id = data["id"]

    @property
    def properties(self) -> list[NotionDatabaseProperty]:
        return [
            NotionDatabaseProperty(data) for data in self._data["properties"].values()
        ]

    def __repr__(self) -> str:
        return "<Db: %s>" % ", ".join([data.__repr__() for data in self.properties])
