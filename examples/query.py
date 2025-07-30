import os
import asyncio
from monitor_api_client import MonitorAPIClient
import logging
import sys
from dotenv import load_dotenv

load_dotenv(".env")


root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

async def examle() -> None:
    client = MonitorAPIClient(
        company_number=os.environ["COMPANY_NUMBER"],
        username=os.environ["API_USERNAME"],
        password=os.environ["API_PASSWORD"],
        host=os.environ["API_HOST"],
    )
    r = await client.query(
        module="Inventory",
        entity="Parts",
        id=1
    )
    print(r)

asyncio.run(examle())