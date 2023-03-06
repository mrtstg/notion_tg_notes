from api.api import NotionApi
from config import FileConfig
import asyncio
import os

CONFIG = FileConfig(os.environ.get("CONFIG_FILE", "config.yaml"))

loop = asyncio.new_event_loop()
api = NotionApi(CONFIG.token, loop)


async def main():
    resp = await api.get_database(CONFIG.db_id)
    print(resp)
    while True:
        pass


if __name__ == "__main__":
    loop.run_until_complete(main())
