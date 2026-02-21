"""Type stubs and utility types for Ghoul Quiz API."""

from typing import Optional, Protocol


class TokenResponse(Protocol):
    """Protocol for token response."""

    access_token: str
    expires_in: int


class QuestionResponse(Protocol):
    """Protocol for question response."""

    id: int
    question: str
    answer_options: list
    answer_group: str


class AnswerRequestOptions(Protocol):
    """Protocol for answer request options."""

    id: Optional[int]
    question: Optional[str]
