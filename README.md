# 🎮 Ghoul Quiz - Асинхронная библиотека и интерактивные игры

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![aiohttp](https://img.shields.io/badge/aiohttp-3.8%2B-blue?style=flat-square)](https://docs.aiohttp.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

Полнофункциональная асинхронная библиотека для работы с **Ghoul Quiz API** (Questions Ghoul) с встроенными интерактивными викторинами из Tokyo Ghoul.

> 📌 **Новое!** Две готовых викторины с разными режимами игры - классическая и расширенная с челленджами!

---

## 🎯 Что это?

**Ghoul Quiz** — это:

1. **📚 Асинхронная библиотека** для работы с API вопросов из Tokyo Ghoul
   - Полная типизация (type hints)
   - Обработка ошибок
   - Автоматическое управление токенами

2. **🎮 Две готовые игры**
   - Классическая викторина (интерактивный и автоматический режимы)
   - Расширенная викторина с 3 режимами: на время, выживание, челлендж

3. **🔐 Полное управление аутентификацией**
   - Временные токены (для гостей)
   - JWT токены (через регистрацию)
   - Автоматическое сохранение и загрузка

---

## ⚡ Быстрый старт (30 секунд)

### 1. Установка

```bash
git clone https://github.com/chestor-cz/ghoul_quiz_lib.git
cd ghoul_quiz_lib
pip install -e .
```

### 2. Запуск игры

```bash
# Классическая викторина
python examples/quiz_game.py

# Расширенная викторина (с режимами)
python examples/quiz_game_advanced.py
```

### 3. Выбрать режим и играть!

```
🎮 ВЫБОР РЕЖИМА
1️⃣  Интерактивный режим (сколько угодно вопросов)
2️⃣  Автоматический режим (5 вопросов)

Выберите режим (1/2): 1
```

---

## 🎮 Игры

### Классическая викторина
**Файл:** `examples/quiz_game.py`

```bash
python examples/quiz_game.py
```

**Функции:**
- ✅ Два режима: интерактивный и автоматический
- ✅ Система подсчета баллов в реальном времени
- ✅ Статистика и история вопросов (сохраняется в JSON)
- ✅ Аутентификация (сохраненные токены, регистрация или гостевой доступ)

**Результаты:**
```
📊 Результаты:
   • Всего вопросов: 10
   • ✅ Правильных: 8
   • ❌ Неправильных: 2
   • 🎯 Точность: 80.0%
   
💾 Статистика сохранена в: ~/.ghoul_quiz/quiz_session_*.json
```

### Расширенная викторина (Профессиональная версия)
**Файл:** `examples/quiz_game_advanced.py`

```bash
python examples/quiz_game_advanced.py
```

**4 игровых режима:**

| Режим | Описание | Где найти очки |
|-------|---------|----------------|
| **⏱️ На время** | 60 секунд, максимум вопросов | Базовые + бонус за скорость |
| **❤️ Выживание** | 3 жизни, потеря при ошибке | По 100 за ответ + бонус за жизни |
| **🚀 Челлендж** | Система мультипликатора (1.0x - 5.0x) | Очки × максимальный мультипликатор |
| **🏆 Рекорды** | Таблица топ-100 результатов | Просмотр и сравнение с другими |

**Пример режима "Челлендж":**
```
🚀 РЕЖИМ ЧЕЛЛЕНДЖ: Растущая сложность!
🎯 Мультипликатор: 1.0x
🔥 Серия: 0

❓ Вопрос #1: Как звали главного антагониста?
Ваш ответ: Аогири

✅ Правильно! Мультипликатор растет: 1.1x

❓ Вопрос #2: ...
```

**Таблица рекордов:**
```
🏆 ТАБЛИЦА РЕКОРДОВ
Место  Игрок          Очки      Режим       Точность
🥇    Chestor         8500      challenge   95.2%
🥈    Player2         7200      time_attack 85.0%
🥉    Player3         6800      survival    72.5%
```

---

## 📚 Библиотека

Используйте библиотеку в своих проектах:

### Простейший пример

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    try:
        # Получить временный токен
        token = await api.get_temporary_token()
        api.set_token(token.access_token)
        
        # Получить вопрос
        question = await api.get_random_question()
        print(f"❓ {question.question}")
        
        # Получить ответ
        answer = await api.get_answer(question.id)
        print(f"✅ {answer.answer}")
    finally:
        await api.close()

asyncio.run(main())
```

### Использование сохраненного токена

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    api = GhoulQuizAPI()
    try:
        # Загрузить сохраненный токен
        if api.load_saved_token("user@example.com"):
            print("✅ Токен загружен")
            
            # Использовать API
            question = await api.get_random_question()
            print(f"Вопрос: {question.question}")
        else:
            print("❌ Токен не найден")
    finally:
        await api.close()

asyncio.run(main())
```

### Регистрация и получение JWT

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def register():
    api = GhoulQuizAPI()
    try:
        # Одна строка для интерактивной регистрации!
        token = await api.register_interactive("user@example.com")
        print(f"✅ Регистрация успешна! JWT: {token}")
    finally:
        await api.close()

asyncio.run(register())
```

### Context Manager

```python
import asyncio
from ghoul_quiz import GhoulQuizAPI

async def main():
    async with GhoulQuizAPI() as api:
        # API автоматически закроется
        question = await api.get_random_question()
        print(question.question)

asyncio.run(main())
```

---

## 🔐 Аутентификация

### Три способа получить доступ:

#### 1. Временный токен (гостевой доступ)
```python
token = await api.get_temporary_token()  # Быстро, без регистрации
api.set_token(token.access_token)        # 10 вопросов в час
```

#### 2. Регистрация и JWT
```python
# Интерактивная регистрация
token = await api.register_interactive("your@email.com")
# Вводите код из письма → получаете JWT
# 1000 вопросов в час!
```

#### 3. Использовать сохраненный токен
```python
api.load_saved_token("your@email.com")  # Из ~/.ghoul_quiz/tokens.json
# Автоматически устанавливает токен
```

---

## 🗂️ Структура проекта

```
ghoul_quiz_lib/
├── ghoul_quiz/                         # Основной пакет
│   ├── __init__.py                     # Экспорты
│   ├── client.py                       # Low-level HTTP клиент
│   ├── session.py                      # High-level API wrapper
│   ├── models.py                       # Data модели
│   ├── register.py                     # Token менеджер
│   └── types.py                        # Type hints
│
├── examples/                           # Примеры и игры
│   ├── quiz_game.py                    # 🎮 Классическая викторина
│   ├── quiz_game_advanced.py           # 🚀 Расширенная викторина
│   ├── QUIZ_GAMES_GUIDE.md            # 📖 Гайд по викторинам
│   ├── demo.py                         # 📝 Базовый пример
│   ├── advanced_examples.py            # 🎯 Продвинутые примеры
│   ├── how_to_use_saved_token.py      # 💾 7 паттернов токенов
│   ├── token_storage_complete_guide.py# ⚙️ Конфигурация
│   └── readme.md                       # 📚 Гайд примеров
│
├── tests/                              # Тесты
│   ├── test_client.py
│   └── test_api.py
│
├── README.md                           # 📖 Этот файл
├── QUIZ_QUICKSTART.md                 # ⚡ Быстрая справка по викторинам
├── QUICKSTART.md                      # 📚 Быстрая справка
├── REGISTRATION_GUIDE.md              # 📋 Гайд регистрации
├── LIBRARY_README.md                  # 📘 Полная документация
├── LIBRARY_STATUS.md                  # ✅ Статус реализации
├── pyproject.toml                      # Poetry конфиг
├── setup.py                            # Setup конфиг
└── requirements-dev.txt                # Dev зависимости
```

---

## 📖 Документация

| Документ | Для кого | Читать |
|----------|---------|--------|
| **QUIZ_QUICKSTART.md** | Хочу быстро начать игру | ⚡ 5 минут |
| **examples/QUIZ_GAMES_GUIDE.md** | Хочу разобраться в викторинах | 📖 15 минут |
| **QUICKSTART.md** | Хочу использовать библиотеку | 📚 10 минут |
| **LIBRARY_README.md** | Хочу все детали API | 📘 30 минут |
| **REGISTRATION_GUIDE.md** | Хочу понять регистрацию | 📋 5 минут |
| **LIBRARY_STATUS.md** | Хочу узнать статус | ✅ 2 минуты |

---

## 🎯 Примеры по сценариям

### "Я хочу просто поиграть"
```bash
python examples/quiz_game.py
```

### "Я хочу соревноваться в режимах"
```bash
python examples/quiz_game_advanced.py
```

### "Я хочу использовать в своем проекте"
```python
from ghoul_quiz import GhoulQuizAPI

async def my_function():
    api = GhoulQuizAPI()
    # Ваш код...
```

### "Я хочу понять как это работает"
```bash
python examples/demo.py                          # Базовый пример
python examples/how_to_use_saved_token.py       # 7 паттернов
python examples/patterns.py                      # Реальные паттерны
```

---

## 🔑 Основные API методы

### Аутентификация

```python
# Получить временный токен
token = await api.get_temporary_token()
api.set_token(token.access_token)

# Регистрировать пользователя
await api.register(email="user@example.com")

# Верифицировать код и получить JWT
response = await api.verify_code(
    email="user@example.com", 
    code="123456"
)
api.set_token(response.token)

# Интерактивная регистрация (одна строка)
await api.register_interactive("user@example.com")
```

### Викторина

```python
# Получить случайный вопрос
question = await api.get_random_question()
print(question.question)

# Получить ответ
answer = await api.get_answer(question.id)
print(answer.answer)
```

### Управление токенами

```python
# Сохранить токен
api.save_token("user@example.com")

# Загрузить токен
api.load_saved_token("user@example.com")

# Показать где хранятся токены
token_file = TokenManager.get_token_file()
print(f"Токены: {token_file}")
```

---

## ⚙️ Конфигурация

### Место сохранения токенов

Автоматически выбирается в зависимости от режима:

```
Разработка: ./.ghoul_quiz/tokens.json          (в папке проекта)
Продакшн:   ~/.ghoul_quiz/tokens.json          (в домашней папке)
Кастом:     export GHOUL_QUIZ_TOKEN_PATH=...   (переменная окружения)
```

### Переопределить API URL

```python
api = GhoulQuizAPI(base_url="http://localhost:3300")
```

### Переопределить путь токенов

```bash
export GHOUL_QUIZ_TOKEN_PATH="/custom/path/tokens.json"
python examples/quiz_game.py
```

---

## 🧪 Тестирование

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest --cov=ghoul_quiz tests/

# Только unit тесты
pytest tests/test_client.py -v
```

---

## 📊 Обработка ошибок

```python
from ghoul_quiz import (
    GhoulQuizAPI,
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    RateLimitError,
    APIError,
)

try:
    question = await api.get_random_question()
except RateLimitError:
    print("⚠️  Превышен лимит запросов")
except UnauthorizedError:
    print("❌ Токен неверный или истек")
except APIError as e:
    print(f"❌ Ошибка API: {e}")
```

---

## 🎯 Лимиты запросов

| Метод | Временный токен | JWT токен |
|-------|-----------------|-----------|
| Регистрация | 10/час | N/A |
| Верификация | 3/час | N/A |
| Получить вопрос | 10/час | 1000/час |
| Получить ответ | 0 | 1000/час |

---

## 📈 Статистика

Все результаты сохраняются автоматически:

```json
{
  "total_questions": 15,
  "correct_answers": 12,
  "accuracy": 80.0,
  "duration_seconds": 300,
  "questions": [
    {
      "id": "q1",
      "text": "Вопрос",
      "answer": "ответ",
      "user_answer": "ответ",
      "is_correct": true
    }
  ]
}
```

Файл сохраняется в: `~/.ghoul_quiz/quiz_session_YYYYMMDD_HHMMSS.json`

---

## 🐛 Решение проблем

### "ModuleNotFoundError: No module named 'ghoul_quiz'"
```bash
pip install -e .
```

### "ConnectionError: Failed to connect"
- Убедитесь, что API запущен: `http://chestor.site:3300`
- Проверьте интернет соединение

### "SSL: CERTIFICATE_VERIFY_FAILED"
- API использует self-signed сертификат
- Библиотека автоматически их игнорирует

### Ошибка "Server disconnected"
- Добавлена автоматическая retry логика (3 попытки)
- Проверьте стабильность соединения с API

---

## 💡 Советы

### 💡 Совет 1: Используйте Context Manager
```python
async with GhoulQuizAPI() as api:
    # API автоматически закроется
    pass
```

### 💡 Совет 2: Сохраняйте токены
```python
api.save_token("user@example.com")
# Позже просто загрузите
api.load_saved_token("user@example.com")
```

### 💡 Совет 3: Обрабатывайте ошибки
```python
try:
    # ваш код
except RateLimitError:
    await asyncio.sleep(60)  # Подождите перед повтором
```

### 💡 Совет 4: Проверьте примеры
```bash
python examples/how_to_use_saved_token.py      # 7 паттернов
python examples/token_storage_complete_guide.py # Конфигурация
```

---

## 📞 Поддержка

- 📖 **Полная документация**: [LIBRARY_README.md](LIBRARY_README.md)
- ⚡ **Быстрая справка**: [QUICKSTART.md](QUICKSTART.md)
- 🎮 **Гайд викторин**: [examples/QUIZ_GAMES_GUIDE.md](examples/QUIZ_GAMES_GUIDE.md)
- 🎯 **Примеры**: [examples/](examples/)

---

## 📄 Лицензия

MIT License - смотрите [LICENSE](LICENSE) для деталей

---

## 👨‍💻 Автор

**CheStor** - [selftopic@gmail.com](mailto:selftopic@gmail.com)

---

## 🎊 Готовы начать?

```bash
# Установить
pip install -e .

# Играть
python examples/quiz_game.py

# Или расширенную версию
python examples/quiz_game_advanced.py
```

**Удачи в викторине! 🚀✨**

---

**Версия**: 0.1.0  
**Python**: >= 3.8  
**Статус**: ✅ Production Ready  
**Последнее обновление**: февраль 2026
