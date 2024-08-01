import httpx
import logging
import json
from typing import Union, List, Dict

logger = logging.getLogger(__name__)

class MonitorAPIException(Exception):
    def __init__(self, message: str, status="", content="") -> None:
        self.message = message
        self.status = status
        self.content = content
        super().__init__(message)

    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}] {self.message}: status `{self.status}` content `{self.content}`"

    def __str__(self) -> str:
        return f"[{self.__class__.__name__}] {self.message}: status `{self.status}` content `{self.content}`"


class MonitorAPI:
    def __init__(self, company_number: str, username: str, password: str, host, port: int=8001, language_code="en", api_version="v1", force_relogin=False) -> None:
        self.port = port
        self.host = host
        self.company_number = company_number
        self.username = username
        self.password = password
        self.language_code = language_code
        self.api_version = api_version
        self.force_relogin = force_relogin

        self.client = httpx.Client(verify=False, timeout=5)
        self.session_id = self.get_latest_session_id()

    @property
    def base_url(self):
        return f"https://{self.host}:{self.port}/{self.language_code}/{self.company_number}"

    def handle_request(self, request: httpx.Request, retry_auth: bool=True) -> Union[List, Dict, str]:
        logger.debug(f"Making a `{request.method}` request to `{request.url}` with headers `{request.headers}` and content `{request.content}`")
        try:
            response = self.client.send(request)
        except (httpx.ConnectTimeout) as e:
            raise MonitorAPIException("Connection timeout")
        except (httpx.ConnectError) as e:
            raise MonitorAPIException("Connection error")
        try:
            data = response.json()
        except json.decoder.JSONDecodeError as e:
            data = response.text
        logger.debug(f"Received response with status `{response.status_code}` and data `{data}`")
        if response.status_code == 200:
            return data
        elif response.status_code == 400:
            raise MonitorAPIException("Bad request", status=response.status_code, content=data)
        elif response.status_code == 401:
            if retry_auth:
                logger.debug("Attempting to authenticate...")
                request.headers["X-Monitor-SessionId"] = self.get_latest_session_id()
                logger.debug("Resending the request...")
                return self.handle_request(request, retry_auth=False)
            else:
                raise MonitorAPIException("Unauthorized", status=response.status_code, content=data)
        elif response.status_code == 403:
            raise MonitorAPIException("Forbidden", status=response.status_code, content=data)
        elif response.status_code == 404:
            raise MonitorAPIException("Query/Command not found", status=response.status_code, content=data)
        elif response.status_code == 409:
            raise MonitorAPIException("Command conflict", status=response.status_code, content=data)
        elif response.status_code == 500:
            raise MonitorAPIException("Server error", status=response.status_code, content=data)
        else:
            raise MonitorAPIException("Unexpected error", status=response.status_code, content=data)

    def get_latest_session_id(self):
        data = self.handle_request(httpx.Request(
            method="POST",
            url=f"{self.base_url}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": self.force_relogin,
            }
        ))
        if data["SessionSuspended"]:
            session_id = data["ActiveSessions"][0]["SessionIdentifier"]
        else:
            session_id = data["SessionId"]
        logger.debug(f"Fetched sessionid `{session_id}`")
        return session_id
    
    def query(self, query: str):
        data= self.handle_request(httpx.Request(
            method="GET",
            url=f"{self.base_url}/api/{self.api_version}/{query}",
            headers={
                "X-Monitor-SessionId": f"{self.session_id}"
            }
        ))
        return data

    def command(self, command: str, body=None):
        data = self.handle_request(httpx.Request(
            method="POST",
            url=f"{self.base_url}/api/{self.api_version}/{command}",
            headers={
                "X-Monitor-SessionId": f"{self.session_id}"
            },
            json=body,
        ))
        return data