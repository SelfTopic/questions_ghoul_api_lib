# 🚀 Быстрый старт

```bash
pip install -e .
```

## Вход и первый вопрос

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

EMAIL = "user@example.com"

async def main():
    async with GhoulQuizAPI() as api:
        # Первый запуск: код придёт на почту. Дальше сессия загружается из файла.
        if not api.load_saved_token(EMAIL):
            await api.register_interactive(EMAIL)

        question = await api.get_random_question()
        print(question.question, question.answer_options)

        answer = await api.get_answer(question_id=question.id)
        print("Ответ:", answer.answer)

asyncio.run(main())
```

Сессия действует 30 дней с момента последнего использования. Токены обновляются автоматически, а новая пара сразу записывается в файл.

## Гостевой доступ

```python
async with GhoulQuizAPI() as api:
    await api.get_temporary_token()           # 1 раз в час с IP, живёт 1 час
    question = await api.get_random_question()  # 10 вопросов в час
    # api.get_answer(...) → AuthenticationRequiredError: ответы только для пользователей
```

## Вход без консоли

```python
await api.register(EMAIL)                              # отправить код
tokens = await api.verify_code(EMAIL, "572286", save_token=True)
print(tokens.access_token, tokens.refresh_token)
```

## Выход

```python
await api.logout()       # эта сессия
await api.logout_all()   # все устройства
```

## Ошибки

```python
from ghoul_quiz import GhoulQuizError, RateLimitError, SessionExpiredError

try:
    question = await api.get_random_question()
except RateLimitError as e:
    print(f"Лимит, повторите через {e.retry_after} с")
except SessionExpiredError:
    print("Сессия закончилась, войдите по email заново")
except GhoulQuizError as e:
    print(f"Ошибка: {e}")
```

## Консольная утилита

```bash
ghoul-quiz-register                                # меню: вход, гость, сессии, выход, статус
ghoul-quiz-register --email user@example.com       # сразу войти
```

## Локальный сервер

```python
GhoulQuizAPI(base_url="http://localhost:3300/api")
```

Подробная документация: [README.md](README.md).
