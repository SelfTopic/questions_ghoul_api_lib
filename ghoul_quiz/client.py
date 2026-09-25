"""Low-level async HTTP transport for the Questions Ghoul API.

Knows nothing about tokens: authentication headers are passed per request
by :class:`ghoul_quiz.session.GhoulQuizAPI`.
"""

import asyncio
from typing import Any, Dict, Optional

import aiohttp

from ghoul_quiz.errors import (
    APIError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from ghoul_quiz.storage import DEFAULT_BASE_URL, normalize_url

_ERRORS_BY_STATUS = {
    400: ValidationError,
    401: UnauthorizedError,
    404: NotFoundError,
    429: RateLimitError,
    503: ServiceUnavailableError,
}


class GhoulAPIClient:
    """Async HTTP client for the API root (e.g. ``https://chestor.site/api``)."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Args:
            base_url: API root including the ``/api`` prefix
            session: aiohttp session to reuse; it is not closed by the client
            timeout: Total timeout per request, seconds
            verify_ssl: Set to False only for local servers with self-signed certificates
        """
        self.base_url = normalize_url(base_url)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.verify_ssl = verify_ssl
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self._session = aiohttp.ClientSession(connector=connector, timeout=self.timeout)
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if the client created it."""
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "GhoulAPIClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @staticmethod
    async def _read_body(response: aiohttp.ClientResponse) -> Any:
        if response.status == 204:
            return None
        if response.content_type == "application/json":
            try:
                return await response.json()
            except (aiohttp.ContentTypeError, ValueError):
                return None
        # Errors from the reverse proxy (502/504 pages) are not JSON.
        return await response.text()

    @staticmethod
    def _raise_for_status(response: aiohttp.ClientResponse, body: Any) -> None:
        if response.ok:
            return
        if isinstance(body, dict):
            message = body.get("error") or response.reason or "Unknown error"
            details = body.get("details")
        else:
            message = response.reason or "Unknown error"
            details = None
        error_class = _ERRORS_BY_STATUS.get(response.status, APIError)
        raise error_class(
            status=response.status,
            message=message,
            details=details,
            headers=dict(response.headers),
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Send a request and return the parsed JSON body (None for 204).

        Args:
            method: HTTP method
            path: Path relative to the API root, e.g. ``/quiz/random``

        Raises:
            ValidationError, UnauthorizedError, NotFoundError, RateLimitError,
            ServiceUnavailableError, APIError: for error statuses
            NetworkError: if the server could not be reached
        """
        session = await self._get_session()
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            async with session.request(method, url, json=json, headers=headers) as response:
                body = await self._read_body(response)
                self._raise_for_status(response, body)
                return body
        except aiohttp.ClientError as e:
            raise NetworkError(f"{method} {url} failed: {e}") from e
        except asyncio.TimeoutError as e:
            raise NetworkError(f"{method} {url} timed out") from e

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        return await self.request("POST", path, json=json, **kwargs)
