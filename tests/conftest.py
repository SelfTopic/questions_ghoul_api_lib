"""In-process fake of the Questions Ghoul API, mirroring the server's auth rules."""

import asyncio
import itertools
import uuid
from typing import Dict, Optional, Set

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from ghoul_quiz import GhoulQuizAPI

CODE = "123456"
QUESTION = {
    "id": 7,
    "question": "Кто главный герой?",
    "answer_options": ["Канеки", "Тоука", "Хидэ", "Ризе"],
    "answer_group": "name",
}
ANSWER = {**QUESTION, "answer": "Канеки"}
del ANSWER["answer_options"]


class FakeAPI:
    def __init__(self) -> None:
        self.counter = itertools.count(1)
        self.guest_tokens: Set[str] = set()
        self.access: Dict[str, str] = {}  # access token -> session (family) id
        self.refresh: Dict[str, dict] = {}  # refresh token -> {"family", "used"}
        self.revoked_families: Set[str] = set()
        self.refresh_calls = 0
        self.requests = []  # (path, headers)
        self.healthy = True
        self.rate_limited = False

    def issue_pair(self, family: Optional[str] = None) -> dict:
        family = family or str(uuid.uuid4())
        n = next(self.counter)
        access, refresh = f"eyJaccess.{n}", f"refresh-{n}"
        self.access[access] = family
        self.refresh[refresh] = {"family": family, "used": False}
        return {
            "accessToken": access,
            "refreshToken": refresh,
            "tokenType": "Bearer",
            "expiresIn": 604800,
            "refreshExpiresIn": 2592000,
        }

    def expire_access_tokens(self) -> None:
        self.access.clear()

    def revoke_family(self, family: str) -> None:
        self.revoked_families.add(family)
        for entry in self.refresh.values():
            if entry["family"] == family:
                entry["used"] = True

    # Middleware-like helpers

    def auth(self, request: web.Request, allow_guest: bool) -> str:
        bearer = request.headers.get("Authorization")
        guest = request.headers.get("X-Temporary-Token")
        if bearer and guest:
            raise error(400, "Передайте только один токен")
        if bearer:
            token = bearer.removeprefix("Bearer ")
            family = self.access.get(token)
            if family is None or family in self.revoked_families:
                raise error(401, "Недействительный или просроченный токен")
            return "user"
        if guest and allow_guest:
            if guest not in self.guest_tokens:
                raise error(401, "Недействительный временный токен")
            return "guest"
        raise error(401, "Требуется Authorization: Bearer <token>")

    # Handlers

    @web.middleware
    async def record(self, request: web.Request, handler):
        self.requests.append((request.path, dict(request.headers)))
        if self.rate_limited and request.path != "/api/health":
            raise web.HTTPTooManyRequests(
                text='{"error": "Слишком много запросов. Попробуйте позже."}',
                content_type="application/json",
                headers={"Retry-After": "42"},
            )
        return await handler(request)

    async def health(self, request):
        if not self.healthy:
            return web.json_response({"ok": False}, status=503)
        return web.json_response({"ok": True})

    async def access_token(self, request):
        token = str(uuid.uuid4())
        self.guest_tokens.add(token)
        return web.json_response({"accessToken": token, "expiresIn": 3600})

    async def register(self, request):
        body = await request.json()
        if "@" not in body.get("email", ""):
            raise error(400, "Неверные входные данные", {"email": ["Некорректный формат email"]})
        return web.json_response({"message": "Код отправлен"})

    async def verify(self, request):
        body = await request.json()
        if body.get("code") != CODE:
            raise error(400, "Неверный код")
        return web.json_response(self.issue_pair())

    async def auth_refresh(self, request):
        self.refresh_calls += 1
        await asyncio.sleep(0.05)  # widen the window for concurrent refreshes
        token = (await request.json())["refreshToken"]
        entry = self.refresh.get(token)
        if entry is None:
            raise error(401, "Недействительный или просроченный refresh-токен")
        if entry["used"]:
            self.revoke_family(entry["family"])
            raise error(401, "Недействительный или просроченный refresh-токен")
        entry["used"] = True
        return web.json_response(self.issue_pair(entry["family"]))

    async def logout(self, request):
        entry = self.refresh.get((await request.json())["refreshToken"])
        if entry:
            self.revoke_family(entry["family"])
        return web.Response(status=204)

    async def logout_all(self, request):
        self.auth(request, allow_guest=False)
        for entry in self.refresh.values():
            self.revoke_family(entry["family"])
        return web.Response(status=204)

    async def random(self, request):
        self.auth(request, allow_guest=True)
        return web.json_response(QUESTION)

    async def answer(self, request):
        self.auth(request, allow_guest=False)
        body = await request.json()
        if body.get("id") not in (None, QUESTION["id"]):
            raise error(404, "Вопрос не найден")
        return web.json_response(ANSWER)

    async def bad_gateway(self, request):
        return web.Response(status=502, text="<html>Bad Gateway</html>", content_type="text/html")

    def app(self) -> web.Application:
        app = web.Application(middlewares=[self.record])
        app.router.add_get("/api/health", self.health)
        app.router.add_get("/api/access_token", self.access_token)
        app.router.add_post("/api/register", self.register)
        app.router.add_post("/api/verify-code", self.verify)
        app.router.add_post("/api/auth/refresh", self.auth_refresh)
        app.router.add_post("/api/auth/logout", self.logout)
        app.router.add_post("/api/auth/logout-all", self.logout_all)
        app.router.add_get("/api/quiz/random", self.random)
        app.router.add_post("/api/quiz/answer", self.answer)
        app.router.add_get("/api/boom", self.bad_gateway)
        return app


def error(status: int, message: str, details: Optional[dict] = None) -> web.HTTPException:
    body = {"error": message, **({"details": details} if details else {})}
    exc_class = {400: web.HTTPBadRequest, 401: web.HTTPUnauthorized, 404: web.HTTPNotFound}[status]
    return exc_class(text=web.json_response(body).text, content_type="application/json")


@pytest.fixture
def token_file(tmp_path, monkeypatch):
    path = tmp_path / "tokens.json"
    monkeypatch.setenv("GHOUL_QUIZ_TOKEN_PATH", str(path))
    return path


@pytest.fixture
async def fake():
    fake = FakeAPI()
    server = TestServer(fake.app())
    await server.start_server()
    fake.base_url = str(server.make_url("/api"))
    yield fake
    await server.close()


@pytest.fixture
async def api(fake, token_file):
    async with GhoulQuizAPI(base_url=fake.base_url) as api:
        yield api
