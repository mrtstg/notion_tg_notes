from abc import ABC, abstractmethod
import datetime


class AbstractPageProperty(ABC):
    property_name: str = ""

    @abstractmethod
    def get_json(self) -> dict:
        pass


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
        return self._timezone

    @timezone.setter
    def timezone(self, value: str | None):
        self._timezone = value

    @property
    def begin_date(self) -> datetime.datetime:
        return self.begin_date

    @begin_date.setter
    def begin_date(self, value: datetime.datetime):
        self._begin_date = value

    @property
    def end_date(self) -> datetime.datetime | None:
        return self._end_date

    @end_date.setter
    def end_date(self, value: datetime.datetime | None):
        self._end_date = value

    def get_json(self) -> dict:
        data = {"start": self._begin_date.isoformat()}
        if self._end_date is not None:
            data["end"] = self._end_date.isoformat()
        if self.timezone is not None:
            data["time_zone"] = self.timezone
        return {self.property_name: {"date": data}}