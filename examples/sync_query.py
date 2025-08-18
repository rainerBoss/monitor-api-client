import os
import asyncio
from monitor.sync_client import SyncMonitorClient
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

def example() -> None:
    client = SyncMonitorClient(
        company_number=os.environ["API_COMPANY_NUMBER"],
        username=os.environ["API_USERNAME"],
        password=os.environ["API_PASSWORD"],
        base_url=os.environ["API_BASE_URL"],
    )
    r = client.query(
        module="Inventory",
        entity="Parts",
        top=1,
        language="lv",
    )
    print(r)

example()