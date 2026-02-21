# 🚀 Быстрый старт

## Самый быстрый способ (3 строки)

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    
    # 1️⃣ Регистрация (интерактивная - введет код в консоль)
    token = await api.register_interactive("your@email.com")
    
    # 2️⃣ Получить вопрос
    question = await api.get_random_question()
    print(f"Вопрос: {question.question}")
    
    # 3️⃣ Получить ответ
    answer = await api.get_answer(question_id=question.id)
    print(f"Ответ: {answer.answer}")
    
    await api.close()

asyncio.run(main())
```

При вызове `register_interactive()` библиотека:
1. Отправит код на вашу почту
2. **Попросит ввести код в консоль** (как в telethon/pyrogram)
3. Получит JWT токен
4. Сохранит его локально
5. Установит его и вернет

## Использование сохраненного токена

Во второй раз просто загрузите сохраненный токен:

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    
    # Загрузить сохраненный токен
    if api.load_saved_token("your@email.com"):
        question = await api.get_random_question()
        print(f"Вопрос: {question.question}")
    
    await api.close()

asyncio.run(main())
```

## Временный токен (для гостей)

Если не хотите регистрироваться:

```python
async def main():
    api = GhoulQuizAPI()
    
    # Получить временный токен (10 вопросов/час)
    temp_token = await api.get_temporary_token()
    api.set_token(temp_token.access_token)
    
    # Можно получать вопросы
    question = await api.get_random_question()
    print(f"Вопрос: {question.question}")
    
    # Но ответы требуют JWT!
    # answer = await api.get_answer(...)  # ❌ Не сработает
    
    await api.close()
```

## Разница между токенами

| | Временный | JWT |
|---|----------|-----|
| **Тип** | UUID | JSON Web Token |
| **Регистрация** | Не требуется | Требуется |
| **Получение** | `get_temporary_token()` | `register_interactive()` |
| **Вопросы** | ✓ (10/час) | ✓ (1000/час) |
| **Ответы** | ❌ | ✓ |
| **Длительность** | 1 час | Долгосрочный |
| **Сохранение** | Нет | Да (~/.ghoul_quiz/tokens.json) |

## API Методы

### Регистрация

```python
# Интерактивная (рекомендуется)
token = await api.register_interactive(
    email="user@example.com",
    save_token=True  # Сохранить после
)

# Или вручную:
await api.register(email="user@example.com")  # Отправить код
token = await api.verify_code(email="user@example.com", code="123456")
api.set_token(token.token)
api.save_token("user@example.com")
```

### Получение вопросов

```python
# Требуется токен (временный или JWT)
question = await api.get_random_question()
# {
#   "id": 123,
#   "question": "Вопрос?",
#   "answer_options": ["Ответ1", "Ответ2", ...],
#   "answer_group": "name"
# }
```

### Получение ответов

```python
# Требуется JWT токен!
answer = await api.get_answer(question_id=question.id)
# или
answer = await api.get_answer(question="Вопрос?")
# {
#   "id": 123,
#   "question": "Вопрос?",
#   "answer": "Правильный ответ",
#   "answer_group": "name"
# }
```

### Управление токенами

```python
# Загрузить сохраненный
api.load_saved_token("user@email.com")

# Сохранить текущий
api.save_token("user@email.com")

# Установить вручную
api.set_token(some_token)

# Получить текущий
current = api.get_token()
```

## Примеры

### Пример 1: Получить 5 вопросов с ответами

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    
    # Регистрация (один раз)
    await api.register_interactive("myemail@example.com")
    
    # Получить 5 вопросов
    for i in range(5):
        q = await api.get_random_question()
        a = await api.get_answer(question_id=q.id)
        print(f"{i+1}. {q.question}")
        print(f"   Ответ: {a.answer}\n")
    
    await api.close()

asyncio.run(main())
```

### Пример 2: Использовать сохраненный токен

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    
    # Загрузить сохраненный (если есть)
    if not api.load_saved_token("myemail@example.com"):
        print("Нет сохраненного токена, регистрируемся...")
        await api.register_interactive("myemail@example.com")
    
    # Использовать
    question = await api.get_random_question()
    print(f"Вопрос: {question.question}")
    
    await api.close()

asyncio.run(main())
```

### Пример 3: Context manager

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    async with GhoulQuizAPI() as api:
        # Регистрация
        await api.register_interactive("myemail@example.com")
        
        # Использовать
        question = await api.get_random_question()
        print(f"Вопрос: {question.question}")
        
        # Автоматически закроется при выходе

asyncio.run(main())
```

## Где сохраняются токены?

Все токены сохраняются в:
```
~/.ghoul_quiz/tokens.json
```

Формат:
```json
{
  "user@example.com": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "api_url": "http://chestor.site:3300"
  }
}
```

## Интерактивный скрипт

Если не хотите писать код, используйте встроенный скрипт:

```bash
# Интерактивное меню
ghoul-quiz-register

# Или прямая регистрация
ghoul-quiz-register --email myemail@example.com
```

## Обработка ошибок

```python
from ghoul_quiz import (
    GhoulQuizAPI,
    ValidationError,
    UnauthorizedError,
    RateLimitError,
    NotFoundError,
    APIError
)

async def main():
    api = GhoulQuizAPI()
    
    try:
        question = await api.get_random_question()
    except UnauthorizedError:
        print("❌ Токен невалиден или истек")
    except RateLimitError:
        print("❌ Превышен лимит запросов")
    except NotFoundError:
        print("❌ Вопрос не найден")
    except ValidationError as e:
        print(f"❌ Ошибка валидации: {e.details}")
    except APIError as e:
        print(f"❌ Ошибка API: {e.message}")
    finally:
        await api.close()

asyncio.run(main())
```

## Готово!

Теперь вы готовы использовать Ghoul Quiz API! 🎉

Начните с:
```python
python quickstart.py
```

Или:
```python
ghoul-quiz-register
```
