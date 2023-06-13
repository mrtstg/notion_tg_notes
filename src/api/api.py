from __future__ import annotations
import datetime
from typing import Any
from config import FileConfig
from api.properties import DatePageProperty, SelectPageProperty, TitlePageProperty
from routes.date_mapper import TodayDateMapper
from . import API_URL
from .structs import NotionDatabase, NotionSearchResult, NotionNote
import aiohttp
import asyncio
from logger import get_logger
import logging

logger = get_logger(__name__, logging.INFO)


class NotionApi:
    _token: str
    client: aiohttp.ClientSession | None = None
    version: str
    config: FileConfig

    def __init__(
        self,
        config: FileConfig,
        event_loop: asyncio.AbstractEventLoop,
        version: str = "2022-06-28",
    ):
        self._token = config.token
        self.config = config
        self.version = version
        event_loop.run_until_complete(self._init_client_session())

    async def _init_client_session(self):
        self.client = aiohttp.ClientSession(
            base_url=API_URL,
            headers={
                "Authorization": f"Bearer {self._token}",
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
        if resp.status != 200:
            raise Exception(await resp.json())
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

    async def get_today_notes(
        self, database_id: str, filter_finished: bool
    ) -> list[NotionNote]:
        notes: list[NotionNote] = []
        now_date = datetime.datetime.now()
        filters: list[dict] = [
            DatePageProperty(
                "Date",
                begin_date=datetime.datetime(
                    now_date.year, now_date.month, now_date.day
                ),
            ).on_or_after_filter,
            DatePageProperty(
                "Date",
                begin_date=datetime.datetime(
                    now_date.year, now_date.month, now_date.day, 23, 59
                ),
            ).on_or_before_filter,
        ]
        if filter_finished:
            filters.append(
                SelectPageProperty(
                    "Progress", self.config.progress_values[-1]
                ).not_equals_filter
            )
        res: NotionSearchResult = await self.query_notes(
            database_id,
            {"and": filters},
        )
        while True:
            notes.extend([NotionNote.from_json(el) for el in res.results])
            if res.next_cursor is None:
                break
            res = await self.load_next_query_page(database_id, res)
        return notes

    async def load_next_query_page(
        self, database_id: str, results: NotionSearchResult, page_size: int = 100
    ) -> NotionSearchResult:
        assert results.next_cursor is not None
        assert self.client is not None
        resp = await self.client.post(
            "/v1/databases/%s/query" % database_id,
            json={
                "start_cursor": results.next_cursor,
                "page_size": page_size,
                "sorts": results._sorts,
            },
        )
        return NotionSearchResult(await resp.json(), results._sorts)

    async def find_today_note_by_title(
        self, database_id: str, title: str
    ) -> NotionNote | None:
        now_date = datetime.datetime.now()
        search_res = await self.query_notes(
            database_id,
            {
                "and": [
                    TitlePageProperty("Title", title).equals_filter,
                    DatePageProperty(
                        "Date",
                        begin_date=datetime.datetime(
                            now_date.year, now_date.month, now_date.day
                        ),
                    ).on_or_after_filter,
                    DatePageProperty(
                        "Date",
                        begin_date=datetime.datetime(
                            now_date.year, now_date.month, now_date.day, 23, 59
                        ),
                    ).on_or_before_filter,
                ]
            },
        )
        if not search_res.results:
            return None
        return NotionNote.from_json(search_res.results[0])

    async def create_today_notes(self, database_id: str, notes: list[dict]):
        for note_data in notes:
            found_note = await self.find_today_note_by_title(
                database_id, note_data["title"]
            )
            if found_note is not None:
                logger.warn("Заметка %s уже существует" % note_data["title"])
                continue
            note = NotionNote()
            note.title.text = note_data["title"]
            note.remind.variants = self.config.default_remind_flags
            note.date.begin_date = TodayDateMapper().get_begin_date()
            note.date.end_date = None
            note.importance.selected = note_data["importance"]
            note.progress.selected = self.config.progress_values[0]
            note.category.variants = note_data["category"]
            try:
                await self.create_note(note, database_id)
            except Exception as e:
                logger.error("Не удалось создать заметку: %s" % e)
                continue
            logger.info("Создана заметка %s" % note_data["title"])

    def __del__(self):
        if self.client is not None:
            asyncio.run(self.client.close())
