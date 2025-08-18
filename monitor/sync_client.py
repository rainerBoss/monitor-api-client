import httpx
import logging
import asyncio
from typing import Any


from .base import BaseMonitorClient
from .import exceptions as exc

logger = logging.getLogger(__name__)

class SyncMonitorClient(BaseMonitorClient):

    def __init__(self, company_number, username, password, base_url, language_code = "en", api_version = "v1", timeout = 10):
        super().__init__(company_number, username, password, base_url, language_code, api_version, timeout)
        self.client = httpx.Client(timeout=timeout)

    def _handle_request(self, request: httpx.Request) -> httpx.Response:
        try:
            response = None
            request = self._refresh_auth_header(request)
            response = self.client.send(request)
            return response
        except httpx.HTTPError as e:
            http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
            raise exc.RequestError(http_error)
        finally:
            self._log_request_response(request, response)

    def login(self) -> None:
        self._login_happening = True
        request = self._create_login_request()
        try:
            response = None
            response = self.client.send(request)
            self._handle_login_response(response)
        except httpx.HTTPError as e:
            http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
            raise exc.RequestError(http_error)
        finally:
            self._log_request_response(request, response)

    def query(self,
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
        response = self._handle_request(request)
        if self._needs_retry(response):
            self.login()
            response = self._handle_request(request)
        return self._handle_query_response(response)

    async def command(self,
        module: str,
        namespace: str,
        command: str,
        many: bool = False,
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
        body: Any | None = None
    ) -> Any:
        request = self._create_command_request(module, namespace, command, body, many, simulate, validate, language)
        response = self._handle_request(request)
        if self._needs_retry(response):
            self.login()
            response = self._handle_request(request)
        return self._handle_command_response(response)

    def batch(self,
        commands: list[dict[str, Any]],
        language: str | None = None
    ) -> Any:
        request = self._create_batch_request(commands, language)
        response = self._handle_request(request)
        if self._needs_retry(response):
            self.login()
            response = self._handle_request(request)
        return self._handle_batch_command_response(response)