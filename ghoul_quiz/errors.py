"""Exceptions raised by the Ghoul Quiz client."""

from typing import Any, Dict, Optional


class GhoulQuizError(Exception):
    """Base class for all library errors."""


class NetworkError(GhoulQuizError):
    """The server could not be reached or the connection failed."""


class AuthenticationRequiredError(GhoulQuizError):
    """Raised before a request when the client has no suitable credentials."""


class APIError(GhoulQuizError):
    """The API answered with an error status.

    The server always responds with ``{"error": "...", "details"?: {...}}``.
    """

    def __init__(
        self,
        status: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status = status
        self.message = message
        self.details = details
        self.headers = headers or {}
        super().__init__(f"API Error {status}: {message}")


class ValidationError(APIError):
    """400: invalid input. ``details`` maps field names to messages."""


class UnauthorizedError(APIError):
    """401: missing, invalid or expired token."""


class SessionExpiredError(UnauthorizedError):
    """The refresh token was rejected: log in by email again.

    Happens when the refresh token expired, the session was logged out,
    or an already used refresh token was presented (the server then
    revokes the whole session).
    """


class NotFoundError(APIError):
    """404: question or route not found."""


class RateLimitError(APIError):
    """429: rate limit exceeded."""

    @property
    def retry_after(self) -> Optional[int]:
        """Seconds to wait, from the ``Retry-After`` header, if the server sent it."""
        value = self.headers.get("Retry-After")
        if value is not None and value.isdigit():
            return int(value)
        return None


class ServiceUnavailableError(APIError):
    """503: the server or one of its dependencies (mail, Redis, Postgres) is down."""
