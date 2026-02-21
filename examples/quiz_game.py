#!/usr/bin/env python3
"""
Полноценная интерактивная игра в викторину на основе Ghoul Quiz API

Функциональность:
✅ Получение вопросов из базы
✅ Интерактивные ответы
✅ Проверка правильности ответов
✅ Система подсчета баллов
✅ Статистика игры
✅ Управление токенами
✅ Режимы игры (легкий/средний/сложный - если поддерживается)
✅ Повторные попытки
✅ История вопросов
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ghoul_quiz import GhoulQuizAPI, TokenManager


@dataclass
class Question:
    """Структура вопроса."""

    id: str
    text: str
    answer: Optional[str] = None
    is_correct: Optional[bool] = None
    user_answer: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GameSession:
    """Статистика сессии."""

    total_questions: int = 0
    correct_answers: int = 0
    wrong_answers: int = 0
    skipped_questions: int = 0
    questions: List[Question] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def accuracy(self) -> float:
        """Процент правильных ответов."""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

    @property
    def duration_seconds(self) -> int:
        """Длительность игры в секундах."""
        start = datetime.fromisoformat(self.start_time)
        return int((datetime.now() - start).total_seconds())

    def save(self, filename: Optional[Path] = None) -> Path:
        """Сохранить статистику в JSON."""
        if filename is None:
            token_dir = TokenManager.get_token_file().parent
            filename = token_dir / f"quiz_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filename.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "wrong_answers": self.wrong_answers,
            "skipped_questions": self.skipped_questions,
            "accuracy": self.accuracy,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "answer": q.answer,
                    "user_answer": q.user_answer,
                    "is_correct": q.is_correct,
                    "timestamp": q.timestamp,
                }
                for q in self.questions
            ],
        }

        filename.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filename


class QuizGame:
    """Главный класс игры в викторину."""

    def __init__(self, api_url: str = "http://chestor.site:3300"):
        """Инициализировать игру."""
        self.api = GhoulQuizAPI(base_url=api_url)
        self.session = GameSession()
        self.running = False

    async def authenticate(self, email: Optional[str] = None) -> bool:
        """Аутентификация пользователя."""
        print("\n" + "=" * 70)
        print("🔐 АУТЕНТИФИКАЦИЯ")
        print("=" * 70)

        if email:
            print(f"\n💾 Проверяю сохраненный токен для {email}...")
            if self.api.load_saved_token(email):
                print(f"✅ Токен загружен для {email}")
                return True
            else:
                print(f"❌ Токен не найден для {email}")

        print("\n1️⃣  Использовать сохраненный токен")
        print("2️⃣  Зарегистрироваться")
        print("3️⃣  Использовать временный токен (гость)")

        choice = input("\nВыберите (1/2/3): ").strip()

        if choice == "1":
            email = input("Введите email: ").strip()
            if self.api.load_saved_token(email):
                print("✅ Токен загружен")
                return True
            else:
                print("❌ Токен не найден")
                return False

        elif choice == "2":
            print("\n📝 Регистрация...")
            email = input("Введите email: ").strip()

            try:
                await self.api.register(email)
                print(f"✅ Ссылка для верификации отправлена на {email}")

                code = input("Введите код верификации: ").strip()
                response = await self.api.verify_code(email, code)

                self.api.set_token(response.token)
                self.api.save_token(email)
                print("✅ Регистрация успешна!")
                return True
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return False

        elif choice == "3":
            try:
                token = await self.api.get_temporary_token()
                self.api.set_token(token.access_token)
                print("✅ Временный токен получен (ограничения: 10 вопросов/час)")
                return True
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return False

        return False

    def print_welcome(self):
        """Показать приветственное сообщение."""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  🎮 ВИКТОРИНА ИЗ TOKYO GHOUL - GHOUL QUIZ  🎮".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "═" * 68 + "╝")
        print("""
Вас ждет увлекательная викторина с вопросами из аниме Tokyo Ghoul!

Правила:
  📌 Каждый раз вам будет предложен случайный вопрос
  📌 Введите свой ответ
  📌 Система проверит правильность
  📌 Ведется счет правильных и неправильных ответов
  📌 В конце игры вы сможете увидеть статистику

Начнем! 🚀
        """)

    async def ask_question(self) -> bool:
        """Попросить и обработать один вопрос."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Получить вопрос
                question_data = await self.api.get_random_question()

                print("\n" + "-" * 70)
                print(f"❓ Вопрос #{self.session.total_questions + 1}")
                print("-" * 70)
                print(f"\n{question_data.question}\n")

                # Показать подсказку
                if hasattr(question_data, "difficulty"):
                    print(f"Сложность: {question_data.difficulty}")  # type: ignore

                # Получить ответ от пользователя
                print("Варианты ответов:")
                print("  → Введите ваш ответ")
                print("  → 'skip' - пропустить")
                print("  → 'quit' - выход")

                user_input = input("\nВаш ответ: ").strip()

                if user_input.lower() == "quit":
                    return False

                if user_input.lower() == "skip":
                    print("⏭️  Вопрос пропущен")
                    self.session.skipped_questions += 1
                    self.session.total_questions += 1
                    q = Question(
                        id=str(question_data.id),
                        text=question_data.question,
                        user_answer="[SKIPPED]",
                        is_correct=False,
                    )
                    self.session.questions.append(q)
                    return True

                # Получить правильный ответ (с retry логикой)
                answer_retry = 0
                answer_data = None
                while answer_retry < max_retries:
                    try:
                        answer_data = await self.api.get_answer(question_data.id)
                        break
                    except Exception:
                        answer_retry += 1
                        if answer_retry < max_retries:
                            print(f"⚠️  Ошибка получения ответа, попытка {answer_retry}...")
                            await asyncio.sleep(1)  # Подождать перед повтором
                        else:
                            raise

                correct_answer = answer_data.answer.lower()
                user_answer = user_input.lower()

                # Проверить ответ
                is_correct = user_answer == correct_answer

                self.session.total_questions += 1
                if is_correct:
                    self.session.correct_answers += 1
                    print("\n✅ ПРАВИЛЬНЫЙ ОТВЕТ!")
                    print(f"   Ответ: {answer_data.answer}")
                else:
                    self.session.wrong_answers += 1
                    print("\n❌ НЕПРАВИЛЬНЫЙ ОТВЕТ!")
                    print(f"   Правильный ответ: {answer_data.answer}")
                    print(f"   Ваш ответ: {user_input}")

                # Сохранить в историю
                q = Question(
                    id=str(question_data.id),
                    text=question_data.question,
                    answer=correct_answer,
                    user_answer=user_answer,
                    is_correct=is_correct,
                )
                self.session.questions.append(q)

                # Показать текущий счет
                print(f"\n📊 Счет: {self.session.correct_answers}/{self.session.total_questions}")
                print(f"📈 Точность: {self.session.accuracy:.1f}%")

                return True

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n⚠️  Ошибка: {e}")
                    print(f"🔄 Попытка подключения {retry_count}/{max_retries}...")
                    await asyncio.sleep(2)  # Подождать перед повтором
                else:
                    print(f"\n❌ Не удалось загрузить вопрос после {max_retries} попыток: {e}")
                    return True  # Продолжить игру, несмотря на ошибку

        return True

    async def play(self, auto_mode: bool = False):
        """Главной цикл игры."""
        self.running = True
        self.print_welcome()

        # Аутентификация
        if not await self.authenticate():
            print("❌ Ошибка аутентификации. Завершение игры.")
            return

        # Основной цикл
        print("\n" + "=" * 70)
        print("🎮 НАЧАЛО ИГРЫ!")
        print("=" * 70)

        if auto_mode:
            # Автоматический режим - N вопросов
            num_questions = 5
            print(f"\n📌 Автоматический режим: {num_questions} вопросов\n")
            for _ in range(num_questions):
                if not await self.ask_question():
                    break
        else:
            # Интерактивный режим
            print("\n📌 Интерактивный режим\n")
            while True:
                if not await self.ask_question():
                    break

                # Предложить продолжить
                if self.session.total_questions > 0 and self.session.total_questions % 5 == 0:
                    cont = input("\n\n⏸️  Продолжить игру? (y/n): ").strip().lower()
                    if cont != "y":
                        break

        # Показать финальную статистику
        await self.show_stats()

    async def show_stats(self):
        """Показать статистику игры."""
        print("\n" + "=" * 70)
        print("📊 СТАТИСТИКА ИГРЫ")
        print("=" * 70)

        if self.session.total_questions == 0:
            print("\n❌ Вопросов не было решено")
            return

        print(f"""
📈 Результаты:
   • Всего вопросов: {self.session.total_questions}
   • ✅ Правильных: {self.session.correct_answers}
   • ❌ Неправильных: {self.session.wrong_answers}
   • ⏭️  Пропущено: {self.session.skipped_questions}
   • 🎯 Точность: {self.session.accuracy:.1f}%
   
⏱️  Время игры: {self.session.duration_seconds // 60} мин {self.session.duration_seconds % 60} сек

🏆 Рейтинг:
   • 90-100%: Мастер викторины! 👑
   • 70-89%:  Хороший результат! 🌟
   • 50-69%:  Неплохо! 👍
   • < 50%:   Нужно больше знаний! 📚
        """)

        if self.session.accuracy >= 90:
            print("   🎉 БЛЕСТЯЩИЙ РЕЗУЛЬТАТ! 🎉")
        elif self.session.accuracy >= 70:
            print("   ⭐ ОТЛИЧНАЯ РАБОТА! ⭐")

        # Сохранить статистику
        stats_file = self.session.save()
        print(f"\n💾 Статистика сохранена: {stats_file}")

    async def close(self):
        """Закрыть соединение."""
        await self.api.close()


async def main():
    """Главная функция."""
    game = QuizGame()

    try:
        # Выбрать режим
        print("\n" + "=" * 70)
        print("🎮 ВЫБОР РЕЖИМА")
        print("=" * 70)
        print("\n1️⃣  Интерактивный режим (сколько угодно вопросов)")
        print("2️⃣  Автоматический режим (5 вопросов)")

        mode = input("\nВыберите режим (1/2): ").strip()
        auto_mode = mode == "2"

        # Играть
        await game.play(auto_mode=auto_mode)

    except KeyboardInterrupt:
        print("\n\n⛔ Игра прервана пользователем")
        await game.show_stats()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        await game.close()


if __name__ == "__main__":
    asyncio.run(main())
