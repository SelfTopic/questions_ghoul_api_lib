"""Ghoul Quiz async library."""

from ghoul_quiz.client import (
    APIError,
    GhoulAPIClient,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)
from ghoul_quiz.models import (
    AnswerResponse,
    QuestionOption,
    RegistrationResponse,
    TemporaryTokenResponse,
    VerifyCodeResponse,
)
from ghoul_quiz.register import TokenManager
from ghoul_quiz.session import GhoulQuizAPI

__version__ = "0.1.0"

__all__ = [
    "GhoulQuizAPI",
    "GhoulAPIClient",
    "TokenManager",
    "APIError",
    "ValidationError",
    "UnauthorizedError",
    "NotFoundError",
    "RateLimitError",
    "TemporaryTokenResponse",
    "RegistrationResponse",
    "VerifyCodeResponse",
    "QuestionOption",
    "AnswerResponse",
]
