import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MonitorApiException(Exception):
    pass

class MonitorAPIClient:
    def __init__(self, company_number: str, username: str, password: str, host: str, port: int=8001, language_code: str="en", api_version: str="v1", force_relogin: bool=False) -> None:
        self.port = port
        self.host = host
        self.company_number = company_number
        self.username = username
        self.password = password
        self.default_language_code = language_code
        self.api_version = api_version
        self.force_relogin = force_relogin

        self.client = httpx.Client(verify=False, timeout=5)
        self.session_id = ""
    
    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"
    
    async def handle_request(self, request: httpx.Request) -> httpx.Response:
        http_error = None
        try:
            async with httpx.AsyncClient(timeout=20, verify=False) as client:
                request.headers["X-Monitor-SessionId"] = self.session_id
                response = await client.send(request)
        except (httpx.HTTPError) as e:
            http_error = e.__doc__.strip() if e.__doc__ else "HTTP Error" 
            raise MonitorApiException(http_error)
        else:
            return response
        finally:
            log_level = logging.DEBUG if not http_error and response.is_success else logging.WARNING
            logger.log(log_level, f"{request.method} Request to {request.url}")
            logger.log(log_level, f"\tHeaders: {request.headers}")
            logger.log(log_level, f"\tContent: {request.content!r}")
            if not http_error:
                logger.log(log_level, f"Response with status {response.status_code}")
                logger.log(log_level, f"\tHeaders: {dict(response.headers)}")
                logger.log(log_level, f"\tContent: {response.content!r}")
            else:
                logger.error(f"Response {http_error}")

    async def login(self) -> None:
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{self.default_language_code}/{self.company_number}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": True,
            }
        )
        response = await self.handle_request(request)
        if response.is_success:
            data = response.json()
            if data["SessionSuspended"]:
                logger.warning("Session suspended")
                raise MonitorApiException("Session suspended")
            else:
                self.session_id = response.headers.get("x-monitor-sessionid")
                logger.debug(f"Refreshed session id: '{self.session_id}'")
                return None
        else:
            logger.warning(f"Login fail with status '{response.status_code}'")
            raise MonitorApiException(f"Login fail with status {response.status_code}")

    async def query(self, module: str, entity: str,
            id: int | None = None,
            language: str | None  = None,
            filter: str  | None = None,
            select: str | None = None,
            expand: str | None = None,
            orderby: str | None = None,
            top: str | None = None,
            skip: str | None = None
        ) -> Any:
        if not language:
            language = self.default_language_code
        request = httpx.Request(
            method="GET",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{entity}/{id if id else ''}",
            params={
                "$filter": filter,
                "$select": select,
                "$expand": expand,
                "$orderby": orderby,
                "$top": top,
                "$skip": skip,
            }
        )
        response = await self.handle_request(request)
        if response.is_success:
            return response.json()
        elif response.status_code == 401: # Refresh session id and retry the request
            await self.login()
            response = await self.handle_request(request)
            if response.is_success:
                return response.json()
        raise MonitorApiException(f"Query for {module}/{entity} failed with status {response.status_code}")

    async def command(self, module: str, namespace: str, command: str, language: str | None = None, body: Any| None = None) -> Any:
        if not language:
            language = self.default_language_code
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{namespace}/{command}",
            json=body,
        )
        response = await self.handle_request(request)
        if response.is_success:
            return response.json()
        elif response.status_code == 401: # Refresh session id and retry the request
            await self.login()
            response = await self.handle_request(request)
            if response.is_success:
                return response.json()
        raise MonitorApiException(f"Command for {module}/{namespace}/{command} failed with status {response.status_code}")

    async def batch(self, commands: list[dict[str, Any]], language: str | None = None) -> Any:
        if not language:
            language = self.default_language_code
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/Batch",
            json=commands,
        )
        response = await self.handle_request(request)
        if response.is_success:
            return response.json()
        elif response.status_code == 401: # Refresh session id and retry the request
            await self.login()
            response = await self.handle_request(request)
            if response.is_success:
                return response.json()
        else:
            raise MonitorApiException(f"Batch command failed with status {response.status_code}")