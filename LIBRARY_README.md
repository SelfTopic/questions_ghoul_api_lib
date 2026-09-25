# Ghoul Quiz Async Library

Асинхронная Python библиотека для работы с API сервиса Ghoul Quiz.

## Основные возможности

- Полностью асинхронный API (asyncio + aiohttp)
- Гостевой доступ (X-Temporary-Token) и пользовательские сессии (JWT access + refresh)
- Автоматическое обновление токенов с защитой одноразового refresh-токена
- Интерактивная регистрация в стиле telethon/pyrogram
- Сохранение токенов в локальной базе данных
- Конфигурируемое хранилище токенов (домашняя папка или проект)
- HTTPS с проверкой сертификата (отключаемой для локальных серверов)
- Типизированные исключения, включая `RateLimitError.retry_after`

## Быстрый старт

```python
from ghoul_quiz import GhoulQuizAPI

async with GhoulQuizAPI() as api:
    if not api.load_saved_token("your@email.com"):
        await api.register_interactive("your@email.com")
    question = await api.get_random_question()
```

## Документация

Подробная документация: [README.md](README.md).
