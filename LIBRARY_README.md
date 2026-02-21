# Ghoul Quiz Async Library

Асинхронная Python библиотека для работы с API сервиса Ghoul Quiz.

## Основные возможности

- Полностью асинхронный API (asyncio + aiohttp)
- Поддержка двух типов токенов: временные (X-Temporary-Token) и JWT (Bearer)
- Интерактивная регистрация в стиле telethon/pyrogram
- Сохранение токенов в локальной базе данных
- Конфигурируемое хранилище токенов (домашняя папка или проект)
- Работа с SSL сертификатами (в том числе самоподписанные)
- Встроенная обработка ошибок и rate limiting

## Быстрый старт

```python
from ghoul_quiz import GhoulQuizAPI

api = GhoulQuizAPI()
await api.register_interactive("your@email.com")
```

## Документация

See [README.md](README.md) для подробной документации.
