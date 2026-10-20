"""Ghoul Quiz async library."""

from ghoul_quiz.client import GhoulAPIClient
from ghoul_quiz.errors import (
    APIError,
    AuthenticationRequiredError,
    GhoulQuizError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    SessionExpiredError,
    UnauthorizedError,
    ValidationError,
)
from ghoul_quiz.models import (
    Answer,
    AnswerResponse,
    GuestToken,
    Media,
    Question,
    QuestionOption,
    RegistrationResponse,
    TemporaryTokenResponse,
    TokenPair,
    TrueFalseAnswer,
    TrueFalseQuestion,
    VerifyCodeResponse,
    WhoisAnswer,
    WhoisQuestion,
)
from ghoul_quiz.session import GhoulQuizAPI
from ghoul_quiz.storage import DEFAULT_BASE_URL, TokenManager

__version__ = "0.3.1"

__all__ = [
    "DEFAULT_BASE_URL",
    "GhoulQuizAPI",
    "GhoulAPIClient",
    "TokenManager",
    # Errors
    "GhoulQuizError",
    "NetworkError",
    "AuthenticationRequiredError",
    "APIError",
    "ValidationError",
    "UnauthorizedError",
    "SessionExpiredError",
    "NotFoundError",
    "RateLimitError",
    "ServiceUnavailableError",
    # Models
    "GuestToken",
    "TokenPair",
    "RegistrationResponse",
    "Question",
    "Answer",
    "Media",
    "WhoisQuestion",
    "WhoisAnswer",
    "TrueFalseQuestion",
    "TrueFalseAnswer",
    # Version 0.1 names
    "TemporaryTokenResponse",
    "VerifyCodeResponse",
    "QuestionOption",
    "AnswerResponse",
]
