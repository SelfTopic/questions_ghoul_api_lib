# 📚 Примеры использования Ghoul Quiz библиотеки

Полная коллекция примеров, от базовых до продвинутых, для работы с асинхронной библиотекой Ghoul Quiz API.

## 🎮 Интерактивные игры (НОВОЕ!)

### 1. Классическая викторина
**Файл:** `quiz_game.py`

Полноценная интерактивная игра с двумя режимами:
- 🎯 Интерактивный режим (бесконечное количество вопросов)
- ⚡ Автоматический режим (5 вопросов)

```bash
python examples/quiz_game.py
```

**Включает:**
- ✅ Интерактивная аутентификация
- ✅ Система подсчета баллов
- ✅ Сохранение статистики в JSON
- ✅ История вопросов и ответов
- ✅ Процент точности
- ✅ Рейтинговая система

### 2. Расширенная викторина (Профессиональная версия)
**Файл:** `quiz_game_advanced.py`

Продвинутая версия с несколькими игровыми режимами:

1. **⏱️ Режим "На время"** - 60 секунд, максимум вопросов
2. **❤️ Режим "Выживание"** - 3 жизни, потеря при ошибке
3. **🚀 Режим "Челлендж"** - Система мультипликатора (1.0x - 5.0x+)
4. **🏆 Таблица рекордов** - Топ-100 результатов

```bash
python examples/quiz_game_advanced.py
```

**Функции:**
- 🎖️ Система достижений
- 📊 Подробная статистика
- 💾 Сохранение рекордов
- ⚡ Различные режимы сложности
- 🔄 Сравнение результатов

📖 **[Полный гайд по викторинам](QUIZ_GAMES_GUIDE.md)**

---

## 📝 Базовые примеры

### Простейший пример
**Файл:** `demo.py`

Получение одного вопроса и ответа:

```bash
python examples/demo.py
```

Демонстрирует:
- Создание API клиента
- Получение временного токена
- Запрос вопроса
- Получение ответа

### Интерактивная регистрация
**Файл:** `advanced_examples.py`

Показывает как использовать методы в асинхронном коде:

```bash
python examples/advanced_examples.py
```

Примеры:
- Использование временных токенов
- Регистрация и верификация
- Работа с JWT токенами
- Обработка ошибок
- Context managers

---

## 🎯 Примеры использования сохраненных токенов

### Как использовать сохраненный токен
**Файл:** `how_to_use_saved_token.py`

7 различных паттернов использования токенов:

```bash
python how_to_use_saved_token.py
```

Демонстрирует:
1. Загрузка токена и использование
2. Прямое задание токена
3. Регистрация и автосохранение
4. Использование в контексте
5. Мульти-аккаунт
6. Синхронный обработчик
7. С обработкой ошибок

---

## 🔐 Конфигурация хранилища токенов

### Автоматическое определение пути
**Файл:** `token_storage_configuration.py`

Базовая демонстрация конфигурации:

```bash
python examples/token_storage_configuration.py
```

Показывает:
- Где сохраняются токены
- Разработка vs Продакшн режимы
- Переменная окружения GHOUL_QUIZ_TOKEN_PATH

### Полный гайд по хранилищу
**Файл:** `token_storage_complete_guide.py`

Комплексный гайд с 4 демо:

```bash
python examples/token_storage_complete_guide.py
```

Демонстрирует:
- Автоматическое определение режима
- Переопределение через env var
- Использование с GhoulQuizAPI
- Лучшие практики

---

## 🚀 Продвинутые примеры

### Паттерны использования
**Файл:** `patterns.py`

Различные паттерны для реальных приложений:

```bash
python examples/patterns.py
```

Включает:
- Error handling
- Retry логика
- Batch обработка
- Parallel requests
- Resource cleanup

### Примеры для продакшена
**Файл:** `production_examples.py`

Production-ready код:

```bash
python examples/production_examples.py
```

Демонстрирует:
- Логирование
- Метрики
- Health checks
- Graceful shutdown
- Configuration management

### Использование токенов
**Файл:** `token_usage.py`

Подробные примеры работы с токенами:

```bash
python examples/token_usage.py
```

Показывает:
- Получение временных токенов
- JWT регистрация
- Сохранение и загрузка
- Управление жизненным циклом

---

## 📊 Регистрация

### Интерактивная регистрация
**Файл:** `register_now.py`

Готовый скрипт для регистрации:

```bash
python register_now.py
```

### Быстрый старт
**Файл:** `quickstart.py`

Минимальный 3-строчный пример:

```bash
python quickstart.py
```

---

## 🗂️ Структура примеров

```
examples/
├── quiz_game.py                      # 🎮 Классическая викторина
├── quiz_game_advanced.py             # 🚀 Расширенная викторина
├── QUIZ_GAMES_GUIDE.md              # 📖 Гайд по викторинам
├── demo.py                           # 📝 Базовый пример
├── advanced_examples.py              # 🎯 Продвинутые примеры
├── patterns.py                       # 🔄 Паттерны использования
├── production_examples.py            # ✅ Production код
├── token_usage.py                    # 🔐 Работа с токенами
├── how_to_use_saved_token.py        # 💾 7 паттернов токенов
├── token_storage_configuration.py    # ⚙️ Конфигурация хранилища
├── token_storage_complete_guide.py  # 📚 Полный гайд хранилища
├── register_now.py                   # 📋 Регистрация
├── quickstart.py                     # ⚡ Быстрый старт (3 строки)
└── readme.md                         # 📖 Этот файл
```

---

## 🚀 Быстрый старт

### Установка

```bash
cd /home/chestor/ghoul_quiz_lib
pip install -e .
```

### Запуск первого примера

```bash
# Классический пример
python examples/demo.py

# Или сразу в игру!
python examples/quiz_game.py
```

---

## 📖 Примеры по сложности

### Уровень 1️⃣ - Начинающий

1. `quickstart.py` - 3 строки кода
2. `demo.py` - Простое получение вопроса
3. `token_usage.py` - Базовая работа с токенами

### Уровень 2️⃣ - Средний

1. `how_to_use_saved_token.py` - 7 паттернов
2. `token_storage_configuration.py` - Конфигурация
3. `advanced_examples.py` - Асинхронные паттерны

### Уровень 3️⃣ - Продвинутый

1. `patterns.py` - Реальные паттерны
2. `production_examples.py` - Production код
3. `token_storage_complete_guide.py` - Полный гайд

### Уровень 4️⃣ - Игры

1. `quiz_game.py` - Интерактивная викторина
2. `quiz_game_advanced.py` - Расширенные режимы

---

## 💡 Типичные сценарии использования

### Сценарий 1: Я хочу просто поиграть
```bash
python examples/quiz_game.py
```

### Сценарий 2: Я хочу научиться использовать библиотеку
```bash
# Начните здесь
python examples/quickstart.py
python examples/demo.py

# Затем
python examples/advanced_examples.py
python examples/patterns.py
```

### Сценарий 3: Я хочу интегрировать в свой проект
```bash
# Изучите
python examples/how_to_use_saved_token.py
python examples/production_examples.py

# Скопируйте нужные части в свой код
```

### Сценарий 4: Я хочу создать свою игру
```bash
# Изучите
python examples/quiz_game.py
python examples/quiz_game_advanced.py

# Используйте как основу для своей игры
```

---

## 📚 Дополнительные ресурсы

- [README.md](../README.md) - Основная документация
- [QUICKSTART.md](../QUICKSTART.md) - Быстрый старт
- [REGISTRATION_GUIDE.md](../REGISTRATION_GUIDE.md) - Гайд регистрации
- [QUIZ_GAMES_GUIDE.md](QUIZ_GAMES_GUIDE.md) - Гайд по викторинам

---

## 🎊 Готовы начать?

Выберите свой путь:

- 🎮 **Хочу сразу поиграть**: `python examples/quiz_game.py`
- 📚 **Хочу учиться**: `python examples/quickstart.py`
- 🚀 **Хочу создавать**: Изучите `examples/patterns.py`

Удачи! 🚀✨
