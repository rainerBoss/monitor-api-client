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
    batch_response = client.batch(
        commands=[
            {
                "Path": "Inventory/Parts/Create",
                "Body": {
                    "PartNumber": "TEST_PART_1",
                    "Description": "test part 1",
                    "Type": 0,
                    "StandardUnitId": 1,
                    "PartTemplateId": {"Value": 1},
                    "Update": None
                },
                "ForwardPropertyName": "EntityId",
                "ReceivingPropertyName": None,
            },
            {
                "Path": "Inventory/Parts/CreateHyperLink",
                "Body": {
                    "Link": "https://api.monitor.se/api/Monitor.API.Inventory.Commands.Parts.CreateHyperLink.html",
                    "Description": "test link"
                },
                "ForwardPropertyName": None,
                "ReceivingPropertyName": "PartId",
            }
        ],
        simulate=True,
        raise_on_error=True
    )
    print(batch_response)

example()