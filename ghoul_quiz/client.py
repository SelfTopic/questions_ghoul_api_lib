"""Async HTTP client for Questions Ghoul API."""

import ssl
from typing import Any, Dict, Optional

import aiohttp


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, status: int, message: str, details: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.details = details
        super().__init__(f"API Error {status}: {message}")


class ValidationError(APIError):
    """Raised when input validation fails (400)."""

    pass


class UnauthorizedError(APIError):
    """Raised when authentication fails (401)."""

    pass


class NotFoundError(APIError):
    """Raised when resource is not found (404)."""

    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""

    pass


class GhoulAPIClient:
    """Async client for Questions Ghoul API."""

    def __init__(
        self,
        base_url: str = "http://chestor.site:3300",
        token: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API
            token: JWT or temporary access token
            session: Optional aiohttp ClientSession to reuse
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            # Create SSL context that accepts self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._owns_session and self._session is not None:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token if available."""
        headers: Dict[str, str] = {"Content-Type": "application/json"}

        if self.token:
            # JWT tokens start with "eyJ", temporary tokens are UUIDs
            if self.token.startswith("eyJ"):  # JWT token
                headers["Authorization"] = f"Bearer {self.token}"
            else:  # Temporary token (UUID format)
                headers["X-Temporary-Token"] = self.token

        return headers

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response and raise errors if needed."""
        data = await response.json()

        if response.status == 400:
            raise ValidationError(
                status=400,
                message=data.get("error", "Validation failed"),
                details=data.get("details"),
            )

        if response.status == 401:
            raise UnauthorizedError(
                status=401,
                message=data.get("error", "Unauthorized"),
            )

        if response.status == 404:
            raise NotFoundError(
                status=404,
                message=data.get("error", "Not found"),
            )

        if response.status == 429:
            raise RateLimitError(
                status=429,
                message=data.get("error", "Rate limit exceeded"),
            )

        if not response.ok:
            raise APIError(
                status=response.status,
                message=data.get("error", "Unknown error"),
                details=data.get("details"),
            )

        return data

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make an async request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (without base URL)
            **kwargs: Additional arguments to pass to session.request()

        Returns:
            Parsed JSON response

        Raises:
            ValidationError: If input validation fails
            UnauthorizedError: If authentication fails
            NotFoundError: If resource not found
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        async with session.request(method, url, headers=headers, **kwargs) as response:
            return await self._handle_response(response)

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", endpoint, **kwargs)

    async def post(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", endpoint, json=json, **kwargs)
