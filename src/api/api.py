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

    def __del__(self):
        if self.client is not None:
            asyncio.run(self.client.close())
