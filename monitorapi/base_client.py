import httpx
import logging
from abc import ABC, abstractmethod
from typing import Any
from .import exceptions as exc


logger = logging.getLogger(__name__)

X_MONITOR_SESSION_ID_HEADER = "x-monitor-sessionid"

class BaseClient(ABC):

    def __init__(self,
        company_number: str,
        username: str,
        password: str,
        base_url: str,
        language_code: str = "en",
        api_version: str = "v1",
        x_monitor_session_id: str | None = None,
        timeout: int = 10
        ) -> None:
        self.company_number = company_number
        self.username = username
        self.password = password
        self.base_url = base_url

        self.language_code = language_code
        self.api_version = api_version
        self.x_monitor_session_id = x_monitor_session_id if x_monitor_session_id else "no-session-id-provided"

        self.timeout = timeout

    @staticmethod
    def _log_request_response(request: httpx.Request, response: httpx.Response | None = None) -> None:
        if response and response.is_error:
            level = logging.WARNING
        elif response:
            level = logging.INFO
        else:
            level = logging.ERROR
        logger.log(level, "Request:")
        logger.log(level, f"URL: {request.url}")
        logger.log(level, f"Headers: {request.headers.items()}")
        logger.log(level, f"Body: {request.content!r}")
        if response:
            logger.log(level, "Response:")
            logger.log(level, f"Status: {response.status_code}")
            logger.log(level, f"Headers: {response.headers.items()}")
            logger.log(level, f"Body: {response.content!r}")

    def _create_login_request(self) -> httpx.Request:
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{self.language_code}/{self.company_number}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": True,
            }
        )
        return request

    def _handle_login_response(self, response: httpx.Response) -> None:
        if response.is_success:
            data = response.json()
            if data["SessionSuspended"]:
                logger.warning("Session suspended")
                raise exc.SessionSuspended(response.text)
            else:
                self.x_monitor_session_id = response.headers.get(X_MONITOR_SESSION_ID_HEADER)
                logger.debug(f"Refreshed session id: '{self.x_monitor_session_id}'")
                return None
        else:
            logger.warning(f"Login failed with status '{response.status_code}'")
            raise exc.LoginFailed(response.text)
    
    def _refresh_auth_header(self, request: httpx.Request) -> httpx.Request:
        request.headers[X_MONITOR_SESSION_ID_HEADER] = self.x_monitor_session_id
        return request

    @abstractmethod
    def login(self) -> None:
        """
        Calls login endpoint and updates the X-Monitor-SessionId.
        Raises:
            RequestError and subtypes
            AuthError and subtypes
        """

    def _general_error_response_handler(self, response: httpx.Response) -> httpx.Response:
        if response.status_code == 401:
            raise exc.InvalidSessionId(response.text)
        if response.status_code == 403:
            if response.text == "Monitor.API is not available for this system":
                raise exc.ApiNotAvailable(response.text)
            else:
                raise exc.SessionSuspended(response.text)
        if response.status_code == 500:
            raise exc.UnhandledException(response.text)
        return response
    
    def _needs_retry(self, response: httpx.Response) -> bool:
        if response.status_code == 401:
            return True
        return False

    def _create_query_request(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: str | None = None
    ) -> httpx.Request:
        if not language:
            language = self.language_code

        if id is None:
            _id = ''
        else:
            _id = str(id)

        params: dict[str, str] = {}
        if filter is not None:
            params["$filter"] = filter
        if select is not None:
            params["$select"] = select
        if expand is not None:
            params["$expand"] = expand
        if orderby is not None:
            params["$orderby"] = orderby
        if top is not None:
            params["$top"] = str(top)
        if skip is not None:
            params["$skip"] = skip

        request = httpx.Request(
            method="GET",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{entity}/{_id}",
            params=params,
        )
        return request
    
    @abstractmethod
    def query(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: str | None = None
    ) -> Any:
        """
        Method for calling API query interface.
        Queries are sent to the API using HTTP GET requests with query parameters that manipulate the way data is fetched and returned.
        They bypass the business domain providing very fast read access of the persistent data of the Monitor ERP system.
        Raises:
            RequestError and subtypes
            GeneralError and subtypes
            QueryError and subtypes
        """
    
    def _handle_query_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            return response.json()
        else:
            if response.status_code == 400:
                if "Id" in response.text:
                    raise exc.QueryInvalidId(response.text)
                else:
                    raise exc.QueryInvalidFilter(response.text)
            if response.status_code == 404:
                raise exc.QueryEntityNotFound(response.text)
            response = self._general_error_response_handler(response)
            raise exc.QueryError(response.text)

    def _create_command_request(self,
        module: str,
        namespace: str,
        command: str,
        body: Any | None = None,
        many: bool = False,
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
    ) -> httpx.Request:
        if not language:
            language = self.language_code
        
        sim_or_val = ""
        if simulate is True:
            sim_or_val = "/Simulate"
        if validate is True:
            sim_or_val = "/Validate"
        
        _many = ""
        if many is True:
            _many = "/Many"
        

        request = httpx.Request(
            method="POST",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{namespace}/{command}{_many}{sim_or_val}",
            json=body,
        )
        return request

    @abstractmethod
    def command(self,
        module: str,
        namespace: str,
        command: str,
        many: bool = False,
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
        body: Any | None = None
    ) -> Any:
        """
        Method for calling API command interface.
        Commands are sent to the API using HTTP POST requests.
        Commands interact with the business domain of the Monitor ERP system.
        Parameters:
            module:
        Returns:
            Any:  
        Raises:
            RequestError and subtypes
            GeneralError and subtypes
            QueryError and subtypes
        """

    def _handle_command_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            else:
                return response.json()
        else:
            if response.status_code == 400:
                raise exc.CommandValidationFailure(response.text)
            if response.status_code == 404:
                if "id" in response.text:
                    raise exc.CommandEntityNotFound(response.text)
                else:
                    raise exc.CommandNotFound(response.text)
            if response.status_code == 409:
                raise exc.CommandConflict(response.text)
            response = self._general_error_response_handler(response)
            raise exc.CommandError(response.text)

    def _create_batch_request(self,
        commands: list[dict[str, Any]],
        language: str | None = None
    ) -> Any:
        if not language:
            language = self.language_code

        request = httpx.Request(
            method="POST",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/Batch",
            json=commands,
        )
        return request
    
    @abstractmethod
    def batch(self,
        commands: list[dict[str, Any]],
        language: str | None = None
    ) -> Any: pass

    def _handle_batch_command_response(self, response: httpx.Response) -> Any:
        return self._handle_command_response(response)