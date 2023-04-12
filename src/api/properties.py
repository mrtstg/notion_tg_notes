from abc import ABC, abstractmethod
import datetime
import pytz
from dataclasses import dataclass


class AbstractPageProperty(ABC):
    property_name: str = ""

    @abstractmethod
    def get_json(self) -> dict:
        pass

    @property
    def ascending_sort(self) -> dict:
        return {"property": self.property_name, "direction": "ascending"}

    @property
    def descending_sort(self) -> dict:
        return {"property": self.property_name, "direction": "descending"}


class TitlePageProperty(AbstractPageProperty):
    _text: str

    def __init__(self, name: str, text: str | None = None):
        self.property_name = name
        if text is not None:
            self._text = text

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text

    def get_json(self) -> dict:
        return {
            self.property_name: {
                "title": [{"type": "text", "text": {"content": self._text}}]
            }
        }

    @property
    def equals_filter(self) -> dict:
        return {"property": self.property_name, "rich_text": {"equals": self.text}}

    @property
    def contains_filter(self) -> dict:
        return {"property": self.property_name, "rich_text": {"contains": self.text}}


class CheckboxPageProperty(AbstractPageProperty):
    _checked: bool

    def __init__(self, name: str, value: bool | None = None):
        self.property_name = name
        if value is not None:
            self._checked = value

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool):
        self._checked = value

    def get_json(self) -> dict:
        assert self.property_name != ""
        return {self.property_name: {"checkbox": self._checked}}

    @property
    def equal_filter(self) -> dict:
        return {"property": self.property_name, "checkbox": {"equals": self.checked}}

    @property
    def not_equal_filter(self) -> dict:
        return {
            "property": self.property_name,
            "checkbox": {"does_not_equal": self.checked},
        }


class SelectPageProperty(AbstractPageProperty):
    _selected: str

    def __init__(self, name: str, value: str | None = None):
        self.property_name = name
        if value is not None:
            self._selected = value

    @property
    def selected(self) -> str:
        return self._selected

    @selected.setter
    def selected(self, value: str):
        self._selected = value

    def get_json(self) -> dict:
        assert self.property_name != ""
        return {self.property_name: {"select": {"name": self.selected}}}

    @property
    def equals_filter(self) -> dict:
        return {"property": self.property_name, "select": {"equals": self._selected}}

    @property
    def not_equals_filter(self) -> dict:
        return {
            "property": self.property_name,
            "select": {"does_not_equal": self._selected},
        }


class MultiSelectPageProperty(AbstractPageProperty):
    _selected: list[str]

    def __init__(self, name: str, variants: list[str] = []):
        self.property_name = name
        self._selected = variants

    @property
    def variants(self) -> list[str]:
        return self._selected

    @variants.setter
    def variants(self, variants: list[str]):
        self._selected = variants

    def get_json(self) -> dict:
        assert self.property_name != ""
        return {
            self.property_name: {
                "multi_select": [{"name": variant} for variant in self.variants]
            }
        }

    def contains_filter(self, variant_name: str) -> dict:
        return {
            "property": self.property_name,
            "multi_select": {"contains": variant_name},
        }

    def not_contains_filter(self, variant_name: str) -> dict:
        return {
            "property": self.property_name,
            "multi_select": {"does_not_contain": variant_name},
        }


@dataclass
class DatePropertyDelta:
    delta: datetime.timedelta
    is_future: bool = True


class DatePageProperty(AbstractPageProperty):
    _timezone: str | None = None
    _begin_date: datetime.datetime
    _end_date: datetime.datetime | None = None

    def __init__(
        self,
        name: str,
        timezone: str | None = None,
        begin_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ):
        self.property_name = name
        if timezone is not None:
            self._timezone = timezone
        if begin_date is not None:
            self._begin_date = begin_date
        if end_date is not None:
            self._end_date = end_date

    @property
    def timezone(self) -> str | None:
        if (self.begin_date.minute == 0 and self.begin_date.second == 0) or (
            self.end_date is None
            or (self.end_date.minute == 0 and self.end_date.second == 0)
        ):
            return None
        return self._timezone

    @timezone.setter
    def timezone(self, value: str | None):
        self._timezone = value

    @property
    def begin_date(self) -> datetime.datetime:
        return self._begin_date

    @begin_date.setter
    def begin_date(self, value: datetime.datetime):
        self._begin_date = value

    @property
    def end_date(self) -> datetime.datetime | None:
        return self._end_date

    @end_date.setter
    def end_date(self, value: datetime.datetime | None):
        self._end_date = value

    @staticmethod
    def stringify_date(date: datetime.datetime) -> str:
        if date.minute != 0 or date.hour != 0:
            return date.isoformat()
        return date.strftime("%Y-%m-%d")

    def get_json(self) -> dict:
        data = {"start": DatePageProperty.stringify_date(self._begin_date)}
        if self._end_date is not None:
            data["end"] = DatePageProperty.stringify_date(self._end_date)
        if self.timezone is not None:
            data["time_zone"] = self.timezone
        return {self.property_name: {"date": data}}

    def _begin_date_filter(self, key: str) -> dict:
        return {
            "property": self.property_name,
            "date": {key: self.stringify_date(self.begin_date)},
        }

    def get_difference(self, prefer_end_date: bool = False) -> DatePropertyDelta:
        date = (
            self.begin_date
            if not prefer_end_date or self.end_date is None
            else self.end_date
        ).replace(tzinfo=pytz.UTC)
        now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
        is_future = now < date
        return DatePropertyDelta(max(now, date) - min(now, date), is_future)

    @property
    def next_week_filter(self) -> dict:
        return {"property": self.property_name, "date": {"next_week": {}}}

    @property
    def equals_filter(self) -> dict:
        return self._begin_date_filter("equals")

    @property
    def after_filter(self) -> dict:
        return self._begin_date_filter("after")

    @property
    def before_filter(self) -> dict:
        return self._begin_date_filter("before")

    @property
    def on_or_after_filter(self) -> dict:
        return self._begin_date_filter("on_or_after")

    @property
    def on_or_before_filter(self) -> dict:
        return self._begin_date_filter("on_or_before")
