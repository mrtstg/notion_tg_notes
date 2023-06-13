from __future__ import annotations
from typing import Any
from . import API_URL
from .structs import NotionDatabase, NotionSearchResult, NotionNote
import aiohttp
import asyncio


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

    def __del__(self):
        if self.client is not None:
            asyncio.run(self.client.close())
