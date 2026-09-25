import asyncio
import json
import os
import stat
import time

import pytest
from conftest import CODE, QUESTION

from ghoul_quiz import (
    APIError,
    AuthenticationRequiredError,
    GhoulQuizAPI,
    NotFoundError,
    RateLimitError,
    SessionExpiredError,
    TokenManager,
    TokenPair,
    ValidationError,
)

EMAIL = "User@Example.com"


async def login(api, email=EMAIL, save=True):
    await api.register(email)
    return await api.verify_code(email, CODE, save_token=save)


async def test_guest_uses_temporary_token_header(api, fake):
    guest = await api.get_temporary_token()
    question = await api.get_random_question()

    assert question.id == QUESTION["id"]
    assert api.auth_type == "guest"
    _, headers = fake.requests[-1]
    assert headers["X-Temporary-Token"] == guest.access_token
    assert "Authorization" not in headers


async def test_guest_cannot_request_answers(api, fake):
    await api.get_temporary_token()
    sent = len(fake.requests)

    with pytest.raises(AuthenticationRequiredError):
        await api.get_answer(question_id=1)
    assert len(fake.requests) == sent


async def test_no_token(api):
    with pytest.raises(AuthenticationRequiredError):
        await api.get_random_question()


async def test_login_sends_only_bearer(api, fake):
    await api.get_temporary_token()
    tokens = await login(api)

    answer = await api.get_answer(question_id=QUESTION["id"])

    assert answer.answer == "Канеки"
    assert tokens.refresh_token and tokens.expires_at > time.time()
    _, headers = fake.requests[-1]
    assert headers["Authorization"] == f"Bearer {tokens.access_token}"
    assert "X-Temporary-Token" not in headers


async def test_verify_code_saves_session(api, token_file):
    tokens = await login(api)

    stored = json.loads(token_file.read_text())["user@example.com"]
    assert stored["refresh_token"] == tokens.refresh_token
    assert stored["api_url"] == api.base_url
    assert stat.S_IMODE(os.stat(token_file).st_mode) == 0o600


async def test_wrong_code(api):
    await api.register(EMAIL)
    with pytest.raises(ValidationError) as exc:
        await api.verify_code(EMAIL, "000000")
    assert exc.value.message == "Неверный код"


async def test_validation_details(api):
    with pytest.raises(ValidationError) as exc:
        await api.register("not-an-email")
    assert exc.value.details == {"email": ["Некорректный формат email"]}


async def test_refresh_on_401_retries_and_persists(api, fake, token_file):
    old = await login(api)
    fake.expire_access_tokens()

    question = await api.get_random_question()

    assert question.id == QUESTION["id"]
    assert fake.refresh_calls == 1
    assert api.tokens.refresh_token != old.refresh_token
    stored = TokenManager.load_session(EMAIL)
    assert stored.refresh_token == api.tokens.refresh_token


async def test_concurrent_requests_refresh_once(api, fake):
    await login(api)
    fake.expire_access_tokens()

    results = await asyncio.gather(*(api.get_random_question() for _ in range(5)))

    assert len(results) == 5
    assert fake.refresh_calls == 1
    assert not fake.revoked_families


async def test_refreshes_before_expiry(api, fake):
    await login(api)
    api.tokens.expires_at = time.time() + 10

    await api.get_random_question()

    assert fake.refresh_calls == 1
    unauthorized = [p for p, _ in fake.requests if p == "/api/quiz/random"]
    assert len(unauthorized) == 1


async def test_no_refresh_when_disabled(fake, token_file):
    async with GhoulQuizAPI(base_url=fake.base_url, auto_refresh=False) as api:
        await login(api)
        fake.expire_access_tokens()
        with pytest.raises(APIError) as exc:
            await api.get_random_question()
        assert exc.value.status == 401
        assert fake.refresh_calls == 0


async def test_reused_refresh_token_ends_session(api, fake, token_file):
    tokens = await login(api)
    fake.refresh[tokens.refresh_token]["used"] = True  # someone else already rotated it
    fake.expire_access_tokens()

    with pytest.raises(SessionExpiredError):
        await api.get_random_question()

    assert api.tokens is None
    assert TokenManager.load_session(EMAIL) is None


async def test_adopts_tokens_rotated_by_another_process(fake, token_file):
    async with (
        GhoulQuizAPI(base_url=fake.base_url) as first,
        GhoulQuizAPI(base_url=fake.base_url) as second,
    ):
        await login(first)
        assert second.load_saved_token(EMAIL)

        fake.expire_access_tokens()
        await first.get_random_question()  # rotates and saves the new pair
        await second.get_random_question()  # must pick it up instead of reusing its old token

        assert not fake.revoked_families
        assert second.tokens.refresh_token == first.tokens.refresh_token


async def test_explicit_refresh(api, fake):
    old = await login(api)
    new = await api.refresh()
    assert new.access_token != old.access_token
    assert fake.refresh_calls == 1


async def test_logout(api, fake, token_file):
    tokens = await login(api)

    await api.logout()

    assert api.tokens is None
    assert TokenManager.load_session(EMAIL) is None
    assert fake.refresh[tokens.refresh_token]["used"]


async def test_logout_all(api, fake):
    await login(api)
    await api.logout_all()
    assert api.tokens is None
    assert fake.revoked_families


async def test_load_saved_session_for_other_server_is_ignored(api, token_file):
    TokenManager.save_session(EMAIL, TokenPair(access_token="eyJx"), api_url="http://other/api")
    assert not api.load_saved_token(EMAIL)


async def test_fully_expired_saved_session_is_deleted(api, token_file):
    past = time.time() - 1
    expired = TokenPair(
        access_token="eyJx", refresh_token="r", expires_at=past, refresh_expires_at=past
    )
    TokenManager.save_session(EMAIL, expired, api_url=api.base_url)

    assert not api.load_saved_token(EMAIL)
    assert TokenManager.load_all() == {}


def test_legacy_storage_entry(token_file):
    token_file.write_text(json.dumps({"a@b.c": {"token": "eyJold", "api_url": "http://x"}}))
    session = TokenManager.load_session("a@b.c")
    assert session.access_token == "eyJold"
    assert session.refresh_token is None
    assert TokenManager.load_token("a@b.c") == "eyJold"


def test_set_token_detects_kind():
    api = GhoulQuizAPI()
    api.set_token("0b1f7e3c-8a4e-4f7a-9c61-2d3b5e6f7a8b")
    assert api.auth_type == "guest"
    api.set_token("eyJhbGciOiJIUzI1NiJ9.x.y")
    assert api.auth_type == "user"
    assert api.get_token() == "eyJhbGciOiJIUzI1NiJ9.x.y"


async def test_get_answer_arguments(api):
    with pytest.raises(ValueError):
        await api.get_answer()
    with pytest.raises(ValueError):
        await api.get_answer(question_id=1, question_text="x")


async def test_not_found(api):
    await login(api)
    with pytest.raises(NotFoundError):
        await api.get_answer(question_id=999)


async def test_rate_limit_retry_after(api, fake):
    fake.rate_limited = True
    with pytest.raises(RateLimitError) as exc:
        await api.get_temporary_token()
    assert exc.value.retry_after == 42


async def test_non_json_error(api):
    with pytest.raises(APIError) as exc:
        await api.client.get("/boom")
    assert exc.value.status == 502


async def test_health(api, fake):
    assert await api.health() is True
    fake.healthy = False
    assert await api.health() is False
