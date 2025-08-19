import os
import logging
import sys
from dotenv import load_dotenv

from monitorapi.sync_client import SyncClient


load_dotenv(".env")

root = logging.getLogger("monitor_erp_api_client")
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

def example() -> None:
    client = SyncClient(
        company_number=os.environ["API_COMPANY_NUMBER"],
        username=os.environ["API_USERNAME"],
        password=os.environ["API_PASSWORD"],
        base_url=os.environ["API_BASE_URL"],
    )
    r = client.query(
        module="Inventory",
        entity="Parts",
        id=1,
    )
    print(r)

example()