import httpx
import logging
from typing import Any, NoReturn
from enum import Enum, auto
from .import exceptions as exc

logger = logging.getLogger(__name__)


class RequestType(Enum):
    QUERY = auto()
    COMMAND = auto()

class MonitorClient:
    def __init__(self,
        company_number: str,
        username: str,
        password: str,
        base_url: str,
        language_code: str="en",
        api_version: str="v1",
        timeout: int = 10
        ) -> None:
        self.company_number = company_number
        self.username = username
        self.password = password
        self.base_url = base_url

        self.language_code = language_code
        self.api_version = api_version
        self.x_monitor_session_id = ""
        
        self.async_http_client = httpx.AsyncClient(timeout=timeout)

    async def send_logged_request(self, request: httpx.Request) -> httpx.Response:
        response = None
        try:
            response = await self.async_http_client.send(request)
            return response
        except httpx.HTTPError as e:
            logger.error("")
            http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
            raise exc.RequestError(http_error)
        finally:
            pass

    async def login(self) -> None:
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{self.language_code}/{self.company_number}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": True,
            }
        )
        response = await self.send_logged_request(request)
        if response.is_success:
            data = response.json()
            if data["SessionSuspended"]:
                logger.warning("Session suspended")
                raise exc.SessionSuspended()
            else:
                self.f = response.headers.get("x-monitor-sessionid")
                logger.debug(f"Refreshed X-Monitor-SessionId: '{self.x_monitor_session_id}'")
                return None
        else:
            logger.warning(f"Login failed with status '{response.status_code}'")
            raise exc.LoginFailed()
        
    async def send_request_with_retry(self, request: httpx.Request) -> httpx.Response:
        response = await self.send_request_with_retry(request)
        if response.status_code == 401: # Refresh session id and retry the request
            await self.login()
            response = await self.send_logged_request(request)
        return response

    def handle_error_response(self, response: httpx.Response, type: RequestType) -> NoReturn:
        if response.status_code == 400:
            if type is RequestType.QUERY:
                if response.text == "Id is not a valid identifier":
                    raise exc.QueryInvalidId()
                elif response.text.startswith("One or more problems were encountered when parsing the filter"):
                    raise exc.QueryInvalidFilter()
                
            if type is RequestType.COMMAND:
                raise exc.CommandValidationFailure()

        if response.status_code == 401:
            raise exc.InvalidSessionId()
        
        if response.status_code == 403:
            if response.text == "Monitor.API is not available for this system":
                raise exc.ApiNotAvailable()
            else:
                raise exc.SessionSuspended()
            
        if response.status_code == 404:
            if type is RequestType.QUERY:
                raise exc.QueryEntityNotFound()
            if type is RequestType.COMMAND:
                raise exc.CommandEntityNotFound()
            
        if response.status_code == 409:
            if type is RequestType.COMMAND:
                raise exc.CommandConflict()
        
        if response.status_code == 500:
            raise exc.InternalMonitorException()
        
        if type is RequestType.QUERY: raise exc.QueryError()
        if type is RequestType.COMMAND: raise exc.CommandError()

    def _create_query_request(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: str | None = None,
        skip: str | None = None
    ) -> httpx.Request:
        if not language:
            language = self.language_code

        if not id:
            _id = ''
        else:
            _id = str(id)

        request = httpx.Request(
            method="GET",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{entity}/{_id}",
            params={
                "$filter": filter,
                "$select": select,
                "$expand": expand,
                "$orderby": orderby,
                "$top": top,
                "$skip": skip,
            }
        )
        return request

    async def query(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: str | None = None,
        skip: str | None = None
    ) -> Any:
        request = self._create_query_request(module, entity, id, language, filter, select, expand, orderby, top, skip)
        response = await self.send_request_with_retry(request)
        if response.is_success:
            return response.json()
        else:
            self.handle_error_response(response, type=RequestType.QUERY)

    def _create_command_request(self,
        module: str,
        namespace: str,
        command: str,
        language: str | None = None,
        body: Any| None = None
    ) -> httpx.Request:
        if not language:
            language = self.language_code

        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{namespace}/{command}",
            json=body,
        )
        return request
    
    async def command(self,
        module: str,
        namespace: str,
        command: str,
        language: str | None = None,
        body: Any | None = None
    ) -> Any:
        request = self._create_command_request(module, namespace, command, language, body)
        response = await self.send_request_with_retry(request)
        if response.is_success:
            return response.json()
        else:
            self.handle_error_response(response, type=RequestType.COMMAND)

    def _create_batch_request(self,
        commands: list[dict[str, Any]],
        language: str | None = None
    ) -> Any:
        if not language:
            language = self.language_code

        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/Batch",
            json=commands,
        )
        return request
    
    async def batch(self,
        commands: list[dict[str, Any]],
        language: str | None = None
    ) -> Any:
        request = self._create_batch_request(commands, language)
        response = await self.send_request_with_retry(request)
        if response.is_success:
            return response.json()
        else:
            self.handle_error_response(response, type=RequestType.COMMAND)