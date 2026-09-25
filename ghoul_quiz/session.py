"""High-level async API for Questions Ghoul Quiz."""

import asyncio
import uuid
from typing import Any, Dict, Optional

import aiohttp

from ghoul_quiz.client import GhoulAPIClient
from ghoul_quiz.errors import (
    AuthenticationRequiredError,
    RateLimitError,
    ServiceUnavailableError,
    SessionExpiredError,
    UnauthorizedError,
    ValidationError,
)
from ghoul_quiz.models import Answer, GuestToken, Question, RegistrationResponse, TokenPair
from ghoul_quiz.storage import DEFAULT_BASE_URL, TokenManager, normalize_email


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


class GhoulQuizAPI:
    """High-level async API for Questions Ghoul Quiz.

    Holds either a user session (access + refresh token) or a guest token.
    With ``auto_refresh`` enabled (default), an expired access token is
    refreshed transparently: before a request if it is about to expire, or
    after a 401. Refresh tokens are single-use, so refreshes never run in
    parallel, and when the session was loaded from or saved to
    :class:`TokenManager`, the new pair is written back immediately.

    Example::

        async with GhoulQuizAPI() as api:
            if not api.load_saved_token("user@example.com"):
                await api.register_interactive("user@example.com")
            question = await api.get_random_question()
            answer = await api.get_answer(question_id=question.id)
    """

    #: Refresh the access token this many seconds before it expires.
    REFRESH_MARGIN = 60

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        auto_refresh: bool = True,
    ):
        """
        Args:
            base_url: API root including ``/api``, e.g. ``http://localhost:3300/api``
            api_key: Access token (JWT) or guest token (UUID) to start with
            session: aiohttp session to reuse
            timeout: Total timeout per request, seconds
            verify_ssl: Set to False only for local servers with self-signed certificates
            auto_refresh: Refresh expired access tokens automatically
        """
        self.client = GhoulAPIClient(
            base_url=base_url, session=session, timeout=timeout, verify_ssl=verify_ssl
        )
        self.auto_refresh = auto_refresh
        self._tokens: Optional[TokenPair] = None
        self._guest: Optional[GuestToken] = None
        # Email the session is persisted under; every rotation is saved there.
        self._email: Optional[str] = None
        self._refresh_lock: Optional[asyncio.Lock] = None
        if api_key:
            self.set_token(api_key)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.close()

    async def __aenter__(self) -> "GhoulQuizAPI":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # State

    @property
    def base_url(self) -> str:
        return self.client.base_url

    @property
    def tokens(self) -> Optional[TokenPair]:
        """Current user session, if any."""
        return self._tokens

    @property
    def guest_token(self) -> Optional[GuestToken]:
        return self._guest

    @property
    def email(self) -> Optional[str]:
        """Email the current session is saved under, if it is persisted."""
        return self._email

    @property
    def auth_type(self) -> Optional[str]:
        """``"user"``, ``"guest"`` or None. A user session takes priority over a guest token."""
        if self._tokens:
            return "user"
        if self._guest:
            return "guest"
        return None

    @property
    def is_authenticated(self) -> bool:
        return self.auth_type is not None

    def set_token(self, token: str) -> None:
        """Set a token of either kind.

        A UUID is treated as a guest token; anything else as a user access
        token without a refresh token (it cannot be refreshed).
        """
        if _is_uuid(token):
            self._guest = GuestToken(access_token=token)
        else:
            self.set_tokens(TokenPair(access_token=token))

    def set_tokens(self, tokens: TokenPair) -> None:
        """Use a user session obtained elsewhere. It is not persisted until :meth:`save_token`."""
        self._tokens = tokens
        self._email = None

    def get_token(self) -> Optional[str]:
        """Access token that will be sent with the next request."""
        if self._tokens:
            return self._tokens.access_token
        if self._guest:
            return self._guest.access_token
        return None

    def clear(self) -> None:
        """Forget all credentials locally (saved sessions are kept)."""
        self._tokens = None
        self._guest = None
        self._email = None

    # Persistence

    def load_saved_token(self, email: str) -> bool:
        """Load the session saved for ``email`` on this server.

        Returns:
            False if there is no usable session (a session whose access and
            refresh tokens have both expired is deleted).
        """
        tokens = TokenManager.load_session(email, api_url=self.base_url)
        if tokens is None:
            return False
        if not tokens.can_refresh and tokens.access_expires_within(0):
            TokenManager.delete(email)
            return False
        self._tokens = tokens
        self._email = normalize_email(email)
        return True

    def save_token(self, email: str) -> bool:
        """Save the current user session under ``email`` and keep it in sync on refresh.

        Returns:
            False if there is no user session (guest tokens are not saved).
        """
        if not self._tokens:
            return False
        TokenManager.save_session(email, self._tokens, api_url=self.base_url)
        self._email = normalize_email(email)
        return True

    def _persist(self) -> None:
        if self._email and self._tokens:
            TokenManager.save_session(self._email, self._tokens, api_url=self.base_url)

    def _drop_session(self) -> None:
        if self._email:
            TokenManager.delete(self._email)
        self._tokens = None
        self._email = None

    # Requests

    def _auth_headers(self, allow_guest: bool) -> Dict[str, str]:
        # The server rejects requests carrying both headers, so exactly one is sent.
        if self._tokens:
            return {"Authorization": f"Bearer {self._tokens.access_token}"}
        if self._guest and allow_guest:
            return {"X-Temporary-Token": self._guest.access_token}
        if self._guest:
            raise AuthenticationRequiredError(
                "This endpoint is for registered users only; guest tokens are not accepted. "
                "Log in with register() + verify_code() or register_interactive()."
            )
        raise AuthenticationRequiredError(
            "No token. Use get_temporary_token(), verify_code() or load_saved_token() first."
        )

    async def _authorized_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        allow_guest: bool = False,
    ) -> Any:
        tokens = self._tokens
        if (
            tokens
            and self.auto_refresh
            and tokens.can_refresh
            and tokens.access_expires_within(self.REFRESH_MARGIN)
        ):
            await self._refresh_if_current(tokens.refresh_token)

        tokens = self._tokens
        headers = self._auth_headers(allow_guest)
        try:
            return await self.client.request(method, path, json=json, headers=headers)
        except UnauthorizedError:
            if not (tokens and self.auto_refresh and tokens.can_refresh):
                raise
            await self._refresh_if_current(tokens.refresh_token)

        headers = self._auth_headers(allow_guest)
        return await self.client.request(method, path, json=json, headers=headers)

    def _lock(self) -> asyncio.Lock:
        # Created lazily: on Python 3.9 a Lock binds to the loop current at creation.
        if self._refresh_lock is None:
            self._refresh_lock = asyncio.Lock()
        return self._refresh_lock

    async def _refresh_if_current(self, seen_refresh_token: Optional[str]) -> None:
        """Refresh unless another coroutine already did it while we waited for the lock."""
        async with self._lock():
            if self._tokens is None or self._tokens.refresh_token != seen_refresh_token:
                return
            await self._do_refresh()

    async def _do_refresh(self) -> None:
        assert self._tokens is not None

        # Another process sharing the token file may have rotated the session already;
        # presenting our (now used) refresh token would get the whole session revoked.
        if self._email:
            stored = TokenManager.load_session(self._email, api_url=self.base_url)
            ours = self._tokens.refresh_token
            if stored and stored.refresh_token and stored.refresh_token != ours:
                self._tokens = stored
                if not stored.access_expires_within(self.REFRESH_MARGIN):
                    return

        refresh_token = self._tokens.refresh_token
        if not refresh_token:
            raise AuthenticationRequiredError("The session has no refresh token.")
        try:
            data = await self.client.post("/auth/refresh", json={"refreshToken": refresh_token})
        except UnauthorizedError as e:
            self._drop_session()
            raise SessionExpiredError(
                status=e.status, message=e.message, details=e.details, headers=e.headers
            ) from e

        self._tokens = TokenPair.from_api(data)
        self._persist()

    async def refresh(self) -> TokenPair:
        """Exchange the refresh token for a new pair right now.

        Raises:
            AuthenticationRequiredError: If there is no refresh token
            SessionExpiredError: If the server rejected the refresh token
        """
        async with self._lock():
            if not (self._tokens and self._tokens.refresh_token):
                raise AuthenticationRequiredError("No refresh token. Log in first.")
            await self._do_refresh()
            assert self._tokens is not None
            return self._tokens

    # Service

    async def health(self) -> bool:
        """True if the server and its database and Redis are up."""
        try:
            data = await self.client.get("/health")
        except ServiceUnavailableError:
            return False
        return bool(isinstance(data, dict) and data.get("ok"))

    # Authentication

    async def get_temporary_token(self) -> GuestToken:
        """Get a guest token and start using it.

        Guests get 10 questions per hour and no answers. The token lives
        1 hour. Rate limit: 1 request/hour per IP.
        """
        data = await self.client.get("/access_token")
        self._guest = GuestToken.from_api(data)
        return self._guest

    async def register(self, email: str) -> RegistrationResponse:
        """Send a 6-digit login code to ``email``.

        The same call is used for sign-up and login: the user is created on
        the first successful :meth:`verify_code`. The code lives 5 minutes;
        a new one can be requested once a minute.

        Raises:
            ValidationError: Invalid email
            RateLimitError: Code already sent less than a minute ago, or hourly limit
            ServiceUnavailableError: The mail service is down
        """
        data = await self.client.post("/register", json={"email": email})
        return RegistrationResponse(message=data["message"])

    async def verify_code(self, email: str, code: str, save_token: bool = False) -> TokenPair:
        """Exchange the emailed code for a session and start using it.

        A code allows 5 attempts, then it has to be requested again.

        Args:
            save_token: Save the session with :class:`TokenManager`

        Raises:
            ValidationError: Wrong, expired or malformed code
        """
        data = await self.client.post("/verify-code", json={"email": email, "code": code})
        self.set_tokens(TokenPair.from_api(data))
        if save_token:
            self.save_token(email)
        assert self._tokens is not None
        return self._tokens

    async def register_interactive(
        self, email: str, save_token: bool = True, max_attempts: int = 3
    ) -> TokenPair:
        """Log in (or sign up) by email, asking for the code in the console.

        Similar to telethon/pyrogram login. Blocks waiting for console input.

        Args:
            save_token: Save the session with :class:`TokenManager` (default True)
            max_attempts: How many times to ask for the code if it is wrong
        """
        print(f"\n📧 Sending a login code to {email}...")
        try:
            response = await self.register(email)
            print(f"✅ {response.message}")
        except RateLimitError as e:
            # Usually "code already sent less than a minute ago": the previous code still works.
            print(f"⚠️  {e.message}")
            print("   If you received a code recently, enter it below.")

        loop = asyncio.get_running_loop()
        for attempt in range(1, max_attempts + 1):
            code = await loop.run_in_executor(None, _ask_code)
            print("🔄 Verifying code...")
            try:
                tokens = await self.verify_code(email, code, save_token=save_token)
            except ValidationError as e:
                print(f"❌ {e.message}")
                if attempt == max_attempts:
                    raise
                continue
            print("✅ Logged in!")
            if save_token:
                print(f"💾 Session saved for {email}")
            return tokens

        raise AssertionError("unreachable")

    login_interactive = register_interactive

    async def logout(self) -> None:
        """End the current session on the server and forget it locally, saved copy included."""
        tokens = self._tokens
        try:
            if tokens and tokens.refresh_token:
                await self.client.post("/auth/logout", json={"refreshToken": tokens.refresh_token})
        finally:
            self._drop_session()

    async def logout_all(self) -> None:
        """End all sessions of the current user on every device."""
        await self._authorized_request("POST", "/auth/logout-all")
        self._drop_session()

    # Quiz

    async def get_random_question(self) -> Question:
        """Get a random question with answer options.

        Works for users and guests. Rate limit: 1000/hour for users, 10/hour for guests.
        """
        data = await self._authorized_request("GET", "/quiz/random", allow_guest=True)
        return Question.from_api(data)

    async def get_answer(
        self, question_id: Optional[int] = None, question_text: Optional[str] = None
    ) -> Answer:
        """Get the correct answer by question ID or text (registered users only).

        Text search ignores case, "ё/е", punctuation and whitespace.

        Raises:
            AuthenticationRequiredError: Only a guest token is available
            NotFoundError: No such question
        """
        if (question_id is None) == (question_text is None):
            raise ValueError("Provide exactly one of question_id or question_text")

        payload: Dict[str, Any] = (
            {"id": question_id} if question_id is not None else {"question": question_text}
        )
        data = await self._authorized_request("POST", "/quiz/answer", json=payload)
        return Answer.from_api(data)


def _ask_code() -> str:
    while True:
        code = input("🔐 Enter the 6-digit code from the email: ").strip()
        if len(code) == 6 and code.isdigit():
            return code
        print("❌ The code consists of 6 digits")
