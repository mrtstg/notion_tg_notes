from . import API_URL
from .structs import NotionDatabase
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
