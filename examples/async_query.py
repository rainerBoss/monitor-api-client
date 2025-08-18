import os
import asyncio
from monitor.async_client import AsyncMonitorClient
import logging
import sys
from dotenv import load_dotenv

load_dotenv(".env")


root = logging.getLogger("monitor")
root.setLevel(logging.WARNING)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

async def examle() -> None:
    client = AsyncMonitorClient(
        company_number=os.environ["API_COMPANY_NUMBER"],
        username=os.environ["API_USERNAME"],
        password=os.environ["API_PASSWORD"],
        base_url=os.environ["API_BASE_URL"],
    )
    r = await  client.query(
        module="Inventory",
        entity="Parts",
        top=1,
        language="lv",
    )
    print(r)


asyncio.run(examle())