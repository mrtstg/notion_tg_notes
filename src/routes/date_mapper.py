from abc import ABC, abstractmethod
import datetime


class AbstractDateMapper(ABC):
    @abstractmethod
    def get_begin_date(self) -> datetime.datetime:
        pass

    @abstractmethod
    def get_end_date(self) -> datetime.datetime | None:
        pass

    @staticmethod
    def now_date() -> datetime.datetime:
        return datetime.datetime.now()


class ClosestWeekDayDateMapper(AbstractDateMapper):
    day: int

    def __init__(self, day: int = 0):
        assert day in [0, 1, 2, 3, 4, 5, 6]
        self.day = day

    def get_begin_date(self) -> datetime.datetime:
        now_date = datetime.datetime.now()
        for day_num in range(1, 8):
            date = datetime.datetime.fromtimestamp(
                datetime.datetime(
                    now_date.year, now_date.month, now_date.day
                ).timestamp()
                + 86400 * day_num
            )
            if date.weekday() == self.day:
                return date
        raise Exception("Unreachable!")

    def get_end_date(self) -> None:
        return None


class TomorrowDateMapper(AbstractDateMapper):
    def get_begin_date(self) -> datetime.datetime:
        now = TomorrowDateMapper.now_date()
        return datetime.datetime(now.year, now.month, now.day + 1)

    def get_end_date(self) -> None:
        return None


class TodayDateMapper(AbstractDateMapper):
    def get_end_date(self) -> datetime.datetime | None:
        return None

    def get_begin_date(self) -> datetime.datetime:
        now = TodayDateMapper.now_date()
        return datetime.datetime(now.year, now.month, now.day)
