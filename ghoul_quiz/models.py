"""API models and response classes."""

from dataclasses import dataclass
from typing import List


@dataclass
class TemporaryTokenResponse:
    """Response from getting temporary access token."""

    access_token: str
    expires_in: int


@dataclass
class RegistrationResponse:
    """Response from registration request."""

    message: str


@dataclass
class VerifyCodeResponse:
    """Response from code verification."""

    token: str


@dataclass
class QuestionOption:
    """A single question from the API."""

    id: int
    question: str
    answer_options: List[str]
    answer_group: str


@dataclass
class AnswerResponse:
    """Response with answer to a question."""

    id: int
    question: str
    answer: str
    answer_group: str
