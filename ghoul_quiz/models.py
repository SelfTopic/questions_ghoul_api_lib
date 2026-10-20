"""API models and response classes."""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GuestToken:
    """Temporary guest token: 10 questions per hour, no access to answers."""

    access_token: str
    expires_in: int = 0
    expires_at: Optional[float] = None

    def __post_init__(self) -> None:
        if self.expires_at is None and self.expires_in:
            self.expires_at = time.time() + self.expires_in

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "GuestToken":
        return cls(access_token=data["accessToken"], expires_in=data["expiresIn"])


@dataclass
class TokenPair:
    """User session: a JWT access token and a single-use refresh token.

    ``expires_at`` and ``refresh_expires_at`` are Unix timestamps computed
    when the pair was received, so a pair loaded from disk knows its age.
    """

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 0
    refresh_expires_in: int = 0
    expires_at: Optional[float] = None
    refresh_expires_at: Optional[float] = None

    def __post_init__(self) -> None:
        now = time.time()
        if self.expires_at is None and self.expires_in:
            self.expires_at = now + self.expires_in
        if self.refresh_expires_at is None and self.refresh_expires_in:
            self.refresh_expires_at = now + self.refresh_expires_in

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "TokenPair":
        return cls(
            access_token=data["accessToken"],
            refresh_token=data["refreshToken"],
            token_type=data.get("tokenType", "Bearer"),
            expires_in=data["expiresIn"],
            refresh_expires_in=data["refreshExpiresIn"],
        )

    def access_expires_within(self, seconds: float) -> bool:
        """True if the access token is known to expire within ``seconds``."""
        return self.expires_at is not None and self.expires_at - time.time() <= seconds

    @property
    def can_refresh(self) -> bool:
        if not self.refresh_token:
            return False
        return self.refresh_expires_at is None or self.refresh_expires_at > time.time()


@dataclass
class RegistrationResponse:
    """Response from ``/register``: the code was sent to the email."""

    message: str


@dataclass
class Media:
    """An image or video attached to a question or an answer."""

    url: str
    kind: str  # "image" or "video"

    @classmethod
    def from_api(cls, data: Optional[Dict[str, Any]]) -> Optional["Media"]:
        """None stays None: the API sends ``null`` when there is no media."""
        if not data:
            return None
        return cls(url=data["url"], kind=data["kind"])


@dataclass
class Question:
    """A random question with answer options (the answer itself is not included)."""

    id: int
    question: str
    answer_options: List[str]
    answer_group: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Question":
        return cls(
            id=data["id"],
            question=data["question"],
            answer_options=data["answer_options"],
            answer_group=data.get("answer_group"),
        )


@dataclass
class Answer:
    """The correct answer to a question (registered users only)."""

    id: int
    question: str
    answer: str
    answer_group: Optional[str] = None
    answer_media: Optional[Media] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Answer":
        return cls(
            id=data["id"],
            question=data["question"],
            answer=data["answer"],
            answer_group=data.get("answer_group"),
            answer_media=Media.from_api(data.get("answerMedia")),
        )


@dataclass
class WhoisQuestion:
    """Who/what is this? A picture or video instead of a question text."""

    id: int
    prompt_media: Media
    answer_options: List[str]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WhoisQuestion":
        media = Media.from_api(data["promptMedia"])
        assert media is not None
        return cls(id=data["id"], prompt_media=media, answer_options=data["answer_options"])


@dataclass
class WhoisAnswer:
    """The correct answer to a "who/what is this?" question (registered users only)."""

    id: int
    answer: str

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WhoisAnswer":
        return cls(id=data["id"], answer=data["answer"])


@dataclass
class TrueFalseQuestion:
    """A statement to judge true or false, optionally with a picture."""

    id: int
    statement: str
    prompt_media: Optional[Media] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "TrueFalseQuestion":
        return cls(
            id=data["id"],
            statement=data["statement"],
            prompt_media=Media.from_api(data.get("promptMedia")),
        )


@dataclass
class TrueFalseAnswer:
    """Whether the statement is true (registered users only)."""

    id: int
    correct: bool

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "TrueFalseAnswer":
        return cls(id=data["id"], correct=data["correct"])


# Names used by version 0.1
TemporaryTokenResponse = GuestToken
VerifyCodeResponse = TokenPair
QuestionOption = Question
AnswerResponse = Answer
