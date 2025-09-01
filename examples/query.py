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
    parts = client.query(
        module="Inventory",
        entity="Parts",
        select="Id,PartNumber",
        expand="PackageType",
        filter="strcontains(PartNumber,69)",
        orderby="PartNumber desc",
        top=5,
        skip=50,
    )
    print(parts)
example()