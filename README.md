# 🎮 Ghoul Quiz: асинхронная библиотека и консольные викторины

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![aiohttp](https://img.shields.io/badge/aiohttp-3.9%2B-blue?style=flat-square)](https://docs.aiohttp.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](#-лицензия)

Асинхронный Python-клиент для **Questions Ghoul API**: базы вопросов викторины по аниме Tokyo Ghoul. API доступен по адресу `https://chestor.site/api`.

В репозитории:

1. **Библиотека `ghoul_quiz`**: вход по коду из письма, пара access/refresh токенов с автоматическим обновлением, гостевой доступ, сохранение сессий, типизированные модели и исключения.
2. **Две консольные викторины** в [examples/](examples/): классическая и расширенная (на время, выживание, челлендж, таблица рекордов).
3. **Консольная утилита** `ghoul-quiz-register` для входа и управления сохранёнными сессиями.

---

## ⚡ Быстрый старт

```bash
git clone https://github.com/chestor-cz/ghoul_quiz_lib.git
cd ghoul_quiz_lib
pip install -e .

python examples/quiz_game.py            # классическая викторина
python examples/quiz_game_advanced.py   # расширенная
```

При первом запуске игра спросит email и пришлёт на него 6-значный код. После входа сессия сохраняется, и повторно вводить код не нужно, пока вы заходите хотя бы раз в 30 дней.

---

## 📚 Библиотека

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    async with GhoulQuizAPI() as api:
        # Сохранённая сессия или вход по коду из письма
        if not api.load_saved_token("user@example.com"):
            await api.register_interactive("user@example.com")

        question = await api.get_random_question()
        print(question.question, question.answer_options)

        answer = await api.get_answer(question_id=question.id)
        print(answer.answer)

asyncio.run(main())
```

### Доступ

| | Гость | Пользователь |
|---|---|---|
| Как получить | `await api.get_temporary_token()` | вход по коду из письма |
| Заголовок | `X-Temporary-Token` | `Authorization: Bearer` |
| Срок жизни | 1 час | access 7 дней, refresh 30 дней с продлением |
| Вопросы | 10 в час | 1000 в час |
| Ответы | ❌ | ✅ |

Библиотека сама выбирает нужный заголовок. Если есть и пользовательская сессия, и гостевой токен, используется сессия: сервер отклоняет запросы, в которых переданы оба.

### Вход по email

Регистрация и вход устроены одинаково: пользователь создаётся при первой успешной проверке кода.

```python
# Интерактивно: код вводится в консоли, сессия сохраняется
tokens = await api.register_interactive("user@example.com")

# Вручную
await api.register("user@example.com")                   # отправить код (живёт 5 минут)
tokens = await api.verify_code("user@example.com", "572286", save_token=True)
```

`verify_code` возвращает `TokenPair` с полями `access_token`, `refresh_token`, `expires_at` и `refresh_expires_at`.

### Автоматическое обновление токенов

Access-токен живёт 7 дней. Когда он истекает, `GhoulQuizAPI` сам обменивает refresh-токен на новую пару. Это происходит заранее, за минуту до истечения, или после ответа `401`, и запрос повторяется.

Refresh-токен **одноразовый**. Если предъявить уже использованный токен, сервер отзовёт всю сессию. Поэтому библиотека:

- никогда не обновляет токены параллельно: одновременные запросы ждут одного обновления;
- сразу записывает новую пару в хранилище, если сессия была загружена оттуда или сохранена туда;
- перед обновлением перечитывает хранилище: если другой процесс уже обновил сессию, берётся его пара.

Если сервер отклонил refresh-токен (срок истёк, был выход или токен использован повторно), выбрасывается `SessionExpiredError`, а сессия удаляется из памяти и хранилища. После этого нужно войти по email заново.

```python
await api.refresh()      # обновить явно
GhoulQuizAPI(auto_refresh=False)   # отключить автообновление
```

### Выход

```python
await api.logout()       # завершить эту сессию на сервере и удалить её локально
await api.logout_all()   # завершить все сессии пользователя на всех устройствах
```

### Методы

| Метод | Эндпоинт | Доступ |
|---|---|---|
| `health()` → `bool` | `GET /health` | все |
| `get_temporary_token()` → `GuestToken` | `GET /access_token` | все |
| `register(email)` → `RegistrationResponse` | `POST /register` | все |
| `verify_code(email, code, save_token=False)` → `TokenPair` | `POST /verify-code` | все |
| `register_interactive(email)` / `login_interactive(email)` → `TokenPair` | оба выше | все |
| `refresh()` → `TokenPair` | `POST /auth/refresh` | пользователь |
| `logout()` | `POST /auth/logout` | пользователь |
| `logout_all()` | `POST /auth/logout-all` | пользователь |
| `get_random_question()` → `Question` | `GET /quiz/random` | гость, пользователь |
| `get_answer(question_id=... \| question_text=...)` → `Answer` | `POST /quiz/answer` | пользователь |

При поиске по `question_text` не учитываются регистр, «ё/е», пунктуация и пробелы.

Состояние клиента: `api.auth_type` (`"user"`, `"guest"` или `None`), `api.tokens`, `api.guest_token`, `api.email`. Токен, полученный в другом месте, можно передать через `set_tokens(TokenPair(...))` или `set_token(str)`. Строка в формате UUID считается гостевым токеном, любая другая строка считается access-токеном без refresh.

### Параметры клиента

```python
GhoulQuizAPI(
    base_url="https://chestor.site/api",  # корень API вместе с /api
    api_key=None,                         # стартовый токен
    session=None,                         # свой aiohttp.ClientSession
    timeout=30.0,
    verify_ssl=True,                      # False только для локального сервера с самоподписанным сертификатом
    auto_refresh=True,
)
```

Для локального сервера: `GhoulQuizAPI(base_url="http://localhost:3300/api")`.

### Исключения

```
GhoulQuizError
├── NetworkError                  сервер недоступен, таймаут
├── AuthenticationRequiredError   нет подходящего токена (например, гость запрашивает ответ)
└── APIError                      .status, .message, .details, .headers
    ├── ValidationError           400, .details содержит ошибки по полям
    ├── UnauthorizedError         401
    │   └── SessionExpiredError   refresh-токен отклонён, нужен вход по email
    ├── NotFoundError             404
    ├── RateLimitError            429, .retry_after в секундах
    └── ServiceUnavailableError   503 (почта, БД или Redis)
```

```python
from ghoul_quiz import RateLimitError, SessionExpiredError

try:
    question = await api.get_random_question()
except RateLimitError as e:
    print(f"Лимит, повторите через {e.retry_after} с")
except SessionExpiredError:
    await api.register_interactive(email)
```

### Хранилище сессий

`TokenManager` хранит сессии в JSON-файле по ключу email и адресу сервера. Файл создаётся с правами `0600`, потому что в нём лежат refresh-токены.

Где лежит файл, определяется так:
1. путь из переменной `GHOUL_QUIZ_TOKEN_PATH`, если она задана;
2. `./.ghoul_quiz/tokens.json`, если в текущей папке есть `pyproject.toml` или `setup.py` (режим разработки);
3. иначе `~/.ghoul_quiz/tokens.json`.

Сессия, сохранённая для другого `base_url`, не загружается. Записи версии 0.1 без refresh-токена читаются, но их access-токен выдан старым сервером, поэтому нужен повторный вход.

---

## 🧰 Консольная утилита

```bash
ghoul-quiz-register                       # меню
ghoul-quiz-register --email user@example.com
ghoul-quiz-register --api-url http://localhost:3300/api
```

Что умеет: вход и регистрация, гостевой токен, проверка, просмотр и завершение сохранённых сессий (на этом устройстве или на всех), проверка статуса сервера.

---

## 🎮 Игры

| Файл | Режимы |
|---|---|
| [examples/quiz_game.py](examples/quiz_game.py) | интерактивный (без ограничения) и автоматический (5 вопросов); статистика сохраняется в JSON |
| [examples/quiz_game_advanced.py](examples/quiz_game_advanced.py) | на время (60 с), выживание (3 жизни), челлендж (множитель до 5x), таблица рекордов |

Для игр нужен вход по email: гостям сервер не отдаёт правильные ответы. Подробнее в [examples/QUIZ_GAMES_GUIDE.md](examples/QUIZ_GAMES_GUIDE.md).

---

## 🎯 Лимиты сервера

| Что | Лимит |
|---|---|
| Любой запрос к `/api` | 120 в минуту с IP |
| Гостевой токен | 1 в час с IP |
| Отправка кода | 10 в час с IP, 5 в час на email, не чаще раза в минуту |
| Проверка кода | 30 в час с IP, 5 попыток на один код |
| Refresh и logout | 60 в час с IP |
| Вопросы и ответы | 10 в час для гостя, 1000 в час для пользователя |

---

## 🧪 Разработка

```bash
pip install -e '.[dev]'
pytest
```

Тесты поднимают внутри процесса фейковый сервер на aiohttp. Он воспроизводит правила настоящего: ротацию refresh-токенов, отзыв сессии при повторном использовании, конфликт двух заголовков, лимиты. Сеть для тестов не нужна.

## 🗂️ Структура

```
ghoul_quiz/
├── session.py    GhoulQuizAPI: методы API и обновление токенов
├── client.py     GhoulAPIClient: HTTP-транспорт, ответы с ошибками превращаются в исключения
├── models.py     GuestToken, TokenPair, Question, Answer
├── errors.py     исключения
├── storage.py    TokenManager: файл сессий
└── register.py   консольная утилита ghoul-quiz-register
examples/         игры и примеры
tests/            тесты с фейковым сервером
```

## 🔄 Переход с 0.1

- Адрес по умолчанию теперь `https://chestor.site/api`, и `base_url` включает `/api`. Проверка SSL включена.
- `verify_code()` возвращает `TokenPair`: вместо `.token` используйте `.access_token`. `register_interactive()` тоже возвращает `TokenPair`, а не строку.
- `get_temporary_token()` сразу включает гостевой токен, вызывать `set_token()` не нужно.
- Без токена выбрасывается `AuthenticationRequiredError`, а не `ValueError`.
- Код подтверждения состоит из 6 цифр.
- Требуется Python 3.9+.
- Старые имена моделей (`TemporaryTokenResponse`, `VerifyCodeResponse`, `QuestionOption`, `AnswerResponse`) остались как псевдонимы.

## 📄 Лицензия

MIT. Автор: CheStor.
