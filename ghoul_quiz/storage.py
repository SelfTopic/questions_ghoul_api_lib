"""Local storage of user sessions (token pairs) in a JSON file."""

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from ghoul_quiz.models import TokenPair

DEFAULT_BASE_URL = "https://chestor.site/api"


def normalize_email(email: str) -> str:
    """Emails are case-insensitive on the server."""
    return email.strip().lower()


def normalize_url(url: str) -> str:
    return url.rstrip("/")


class TokenManager:
    """Store and load user sessions locally, keyed by email.

    Token storage location is determined automatically:

    1. ``GHOUL_QUIZ_TOKEN_PATH`` environment variable, if set.
    2. ``./.ghoul_quiz/tokens.json`` if ``setup.py`` or ``pyproject.toml`` is in the
       current directory (development mode).
    3. ``~/.ghoul_quiz/tokens.json`` otherwise.

    The file holds refresh tokens valid for 30 days, so it is created with
    ``0600`` permissions and rewritten atomically.

    File format::

        {
          "user@example.com": {
            "api_url": "https://chestor.site/api",
            "access_token": "eyJ...",
            "refresh_token": "q3Z...",
            "expires_at": 1790000000.0,
            "refresh_expires_at": 1792000000.0
          }
        }

    Entries written by version 0.1 (``{"token": ..., "api_url": ...}``) are still
    readable as sessions without a refresh token.
    """

    @classmethod
    def get_token_file(cls) -> Path:
        custom_path = os.environ.get("GHOUL_QUIZ_TOKEN_PATH")
        if custom_path:
            return Path(custom_path)

        current_dir = Path.cwd()
        if (current_dir / "setup.py").exists() or (current_dir / "pyproject.toml").exists():
            return current_dir / ".ghoul_quiz" / "tokens.json"

        return Path.home() / ".ghoul_quiz" / "tokens.json"

    @classmethod
    def load_all(cls) -> Dict[str, Dict[str, Any]]:
        """Raw contents of the token file; empty if missing or corrupted."""
        token_file = cls.get_token_file()
        if not token_file.exists():
            return {}
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    @classmethod
    def _write_all(cls, data: Dict[str, Dict[str, Any]]) -> None:
        token_file = cls.get_token_file()
        token_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(dir=token_file.parent, prefix=".tokens-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, token_file)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    @classmethod
    def save_session(cls, email: str, tokens: TokenPair, api_url: str = DEFAULT_BASE_URL) -> None:
        """Save (or replace) the session for ``email``."""
        data = cls.load_all()
        entry = asdict(tokens)
        # Durations are relative to the moment the pair was issued; only timestamps are meaningful.
        entry.pop("expires_in", None)
        entry.pop("refresh_expires_in", None)
        data[normalize_email(email)] = {"api_url": normalize_url(api_url), **entry}
        cls._write_all(data)

    @classmethod
    def load_session(cls, email: str, api_url: Optional[str] = None) -> Optional[TokenPair]:
        """Load the session for ``email``.

        If ``api_url`` is given, a session saved for a different server is ignored.
        """
        entry = cls.load_all().get(normalize_email(email))
        if not isinstance(entry, dict):
            return None
        saved_url = normalize_url(entry.get("api_url", ""))
        if api_url is not None and saved_url != normalize_url(api_url):
            return None

        access_token = entry.get("access_token") or entry.get("token")
        if not access_token:
            return None
        return TokenPair(
            access_token=access_token,
            refresh_token=entry.get("refresh_token"),
            token_type=entry.get("token_type", "Bearer"),
            expires_at=entry.get("expires_at"),
            refresh_expires_at=entry.get("refresh_expires_at"),
        )

    @classmethod
    def delete(cls, email: str) -> bool:
        """Delete the saved session. Returns False if there was none."""
        data = cls.load_all()
        if data.pop(normalize_email(email), None) is None:
            return False
        cls._write_all(data)
        return True

    @classmethod
    def get_api_url(cls, email: str) -> Optional[str]:
        entry = cls.load_all().get(normalize_email(email))
        return entry.get("api_url") if isinstance(entry, dict) else None

    # Version 0.1 interface

    @classmethod
    def save_token(cls, email: str, token: str, api_url: str = DEFAULT_BASE_URL) -> None:
        """Save a bare access token (no refresh token)."""
        cls.save_session(email, TokenPair(access_token=token), api_url)

    @classmethod
    def load_token(cls, email: str) -> Optional[str]:
        session = cls.load_session(email)
        return session.access_token if session else None

    @classmethod
    def load_all_tokens(cls) -> Dict[str, Dict[str, Any]]:
        return cls.load_all()

    @classmethod
    def delete_token(cls, email: str) -> bool:
        return cls.delete(email)

    @classmethod
    def get_token_api_url(cls, email: str) -> Optional[str]:
        return cls.get_api_url(email)
