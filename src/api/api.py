from __future__ import annotations
import datetime
from typing import Any
from . import API_URL
from .structs import NotionDatabase
from .properties import (
    CheckboxPageProperty,
    DatePageProperty,
    SelectPageProperty,
    MultiSelectPageProperty,
    TitlePageProperty,
)
import aiohttp
import asyncio


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
        self.date = DatePageProperty("Date")
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


class NotionApi:
    client: aiohttp.ClientSession | None = None
    token: str
    version: str

    def __init__(
        self,
        token: str,
        event_loop: asyncio.AbstractEventLoop,
        version: str = "2022-06-28",
    ):
        self.token = token
        self.version = version
        event_loop.run_until_complete(self._init_client_session())

    async def _init_client_session(self):
        self.client = aiohttp.ClientSession(
            base_url=API_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": self.version,
            },
        )

    async def get_page(self, page_id: str) -> aiohttp.ClientResponse:
        assert self.client is not None
        resp = await self.client.get("/v1/pages/%s" % page_id)
        resp.raise_for_status()
        return resp

    async def get_database(self, database_id: str) -> NotionDatabase:
        assert self.client is not None
        resp = await self.client.get("/v1/databases/%s" % database_id)
        resp.raise_for_status()
        data = await resp.json()
        return NotionDatabase(data)

    async def create_note(self, note: NotionNote, database_id: str) -> dict:
        assert self.client is not None
        resp = await self.client.post(
            "/v1/pages",
            json={
                "parent": {"database_id": database_id},
                "properties": note.get_json(),
            },
        )
        resp.raise_for_status()
        return await resp.json()

    async def query_notes(
        self,
        database_id: str,
        filters: list[dict] | dict = {},
        sorts: list[dict] = [],
        page_size: int = 100,
    ) -> NotionSearchResult:
        assert self.client is not None
        payload: dict[str, Any] = {"page_size": page_size}
        if sorts:
            payload["sorts"] = sorts
        if filters != {}:
            payload["filter"] = filters
        resp = await self.client.post(
            "/v1/databases/%s/query" % database_id, json=payload
        )
        resp.raise_for_status()
        return NotionSearchResult(await resp.json(), sorts)

    async def load_next_query_page(
        self, database_id: str, results: NotionSearchResult, page_size: int = 100
    ) -> NotionSearchResult:
        assert results.next_cursor is not None
        assert self.client is not None
        resp = await self.client.post(
            "/v1/databases/%s/query" % database_id,
            json={
                "start_cursor": results.next_cursor,
                "page_size": 100,
                "sorts": results._sorts,
            },
        )
        return NotionSearchResult(await resp.json(), results._sorts)

    def __del__(self):
        if self.client is not None:
            asyncio.run(self.client.close())
