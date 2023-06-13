from __future__ import annotations
import enum
from typing import Any
import datetime
from .properties import (
    CheckboxPageProperty,
    DatePageProperty,
    SelectPageProperty,
    MultiSelectPageProperty,
    TitlePageProperty,
)


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


class NotionSearchResult:
    _sorts: list[dict]
    results: list[dict]
    has_more: bool
    next_cursor: str | None = None

    def __init__(self, data: dict, sorts: list[dict]):
        self._sorts = sorts
        self.results = data["results"]
        self.has_more = data["has_more"]
        if self.has_more:
            self.next_cursor = data["next_cursor"]


class NotionNote:
    title: TitlePageProperty
    remind: CheckboxPageProperty
    date: DatePageProperty
    importance: SelectPageProperty
    progress: SelectPageProperty
    category: MultiSelectPageProperty

    def __init__(self):
        self.title = TitlePageProperty("Title")
        self.remind = CheckboxPageProperty("Remind")
        self.date = DatePageProperty("Date", "Europe/Moscow")
        self.importance = SelectPageProperty("Importance")
        self.progress = SelectPageProperty("Progress")
        self.category = MultiSelectPageProperty("Category")

    @staticmethod
    def from_json(page: dict) -> NotionNote:
        properties: dict = page["properties"]
        obj = NotionNote()
        obj.remind.checked = properties["Remind"]["checkbox"]
        obj.title.text = properties["Title"]["title"][0]["text"]["content"]
        obj.importance.selected = properties["Importance"]["select"]["name"]
        obj.progress.selected = properties["Progress"]["select"]["name"]
        obj.category.variants = list(
            map(lambda x: x["name"], properties["Category"]["multi_select"])
        )
        for attr, key in {
            "begin_date": "start",
            "end_date": "end",
            "timezone": "time_zone",
        }.items():
            value: str | None = properties["Date"]["date"][key]
            if "date" in attr and value is not None:
                setattr(obj.date, attr, datetime.datetime.fromisoformat(value))
                continue
            setattr(obj.date, attr, value)
        return obj

    def represent(self) -> str:
        def _format_date(date: datetime.datetime) -> str:
            now = datetime.datetime.now()
            is_zero_time = date.minute == 0 and date.hour == 0
            is_today = (
                date.year == now.year
                and date.month == now.month
                and date.day == now.day
            )

            if is_zero_time and not is_today:
                return date.strftime("%d.%m")

            if not is_zero_time and not is_today:
                return date.strftime("%d.%m %H:%M")

            if not is_zero_time and is_today:
                return date.strftime("%H:%M")

            return ""

        importance: str | None = None
        delta_class = self.date.get_difference(True)
        minutes = delta_class.delta.seconds / 60
        hours, minutes = divmod(minutes, 60)
        match self.importance.selected:
            case "Важно":
                importance = "🔴"
            case "Неважно":
                importance = "⚪"
            case "Срочно":
                importance = "🔥"

        delta_text = _format_date(delta_class.date_compared_to)
        delta_text = f" [{delta_text}] " if delta_text != "" else delta_text
        return "%(importance)s%(delta_text)s %(title)s" % {
            "delta_text": delta_text,
            "importance": importance,
            "title": self.title_value,
        }

    @property
    def title_value(self) -> str:
        return self.title.text

    @property
    def remind_value(self) -> bool:
        return self.remind.checked

    @property
    def begin_date_value(self) -> datetime.datetime:
        return self.date.begin_date

    @property
    def end_date_value(self) -> datetime.datetime | None:
        return self.date.end_date

    @property
    def importance_value(self) -> str:
        return self.importance.selected

    @property
    def progress_value(self) -> str:
        return self.progress.selected

    @property
    def categories_value(self) -> list[str]:
        return self.category.variants

    def get_json(self) -> dict:
        data = {}
        for i in [
            self.title,
            self.remind,
            self.date,
            self.importance,
            self.progress,
            self.category,
        ]:
            data.update(i.get_json())
        return data
