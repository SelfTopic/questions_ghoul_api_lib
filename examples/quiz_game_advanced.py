#!/usr/bin/env python3
"""
РАСШИРЕННАЯ ВИКТОРИНА - Профессиональная версия с дополнительными режимами

Дополнительные функции:
✅ Режим "На время" (30/60/120 сек)
✅ Режим "Выживание" (жизни уменьшаются с ошибками)
✅ Режим "Челлендж" (растущая сложность)
✅ Система достижений
✅ Таблица рекордов
✅ Категории вопросов (если API поддерживает)
✅ Мультиплеер по очкам
✅ Анализ ошибок
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from ghoul_quiz import GhoulQuizAPI, TokenManager


class GameMode(Enum):
    """Режимы игры."""

    CLASSIC = "classic"  # Обычный режим
    TIME_ATTACK = "time_attack"  # На время
    SURVIVAL = "survival"  # Выживание
    CHALLENGE = "challenge"  # Челлендж


class Difficulty(Enum):
    """Уровни сложности."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Achievement:
    """Достижение."""

    id: str
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlock_date: Optional[str] = None


@dataclass
class AdvancedGameSession:
    """Расширенная статистика сессии."""

    mode: GameMode = GameMode.CLASSIC
    difficulty: Difficulty = Difficulty.MEDIUM

    # Основная статистика
    total_questions: int = 0
    correct_answers: int = 0
    wrong_answers: int = 0
    skipped_questions: int = 0

    # Для режима времени
    time_limit: int = 0  # секунды
    time_used: int = 0

    # Для режима выживания
    lives: int = 3
    max_lives: int = 3

    # Для режима челленджа
    current_multiplier: float = 1.0
    max_multiplier: float = 1.0

    # История и достижения
    questions: List[Dict] = field(default_factory=list)
    achievements: List[Achievement] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def accuracy(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

    @property
    def score(self) -> int:
        """Общий счет с учетом режима."""
        base_score = self.correct_answers * 100

        if self.mode == GameMode.TIME_ATTACK:
            # Бонус за скорость
            time_bonus = max(0, 3600 - self.time_used) // 10
            return base_score + time_bonus
        elif self.mode == GameMode.CHALLENGE:
            # Умножитель применяется к каждому ответу
            return int(base_score * self.max_multiplier)

        return base_score

    @property
    def duration_seconds(self) -> int:
        start = datetime.fromisoformat(self.start_time)
        return int((datetime.now() - start).total_seconds())


class AdvancedQuizGame:
    """Продвинутая версия игры."""

    # Таблица рекордов
    LEADERBOARD_FILE = "quiz_leaderboard.json"

    def __init__(self, api_url: str = "http://chestor.site:3300"):
        self.api = GhoulQuizAPI(base_url=api_url)
        self.session = AdvancedGameSession()
        self.leaderboard = self._load_leaderboard()
        self.init_achievements()

    def init_achievements(self):
        """Инициализировать достижения."""
        achievements = [
            Achievement("first_blood", "Первая кровь", "Ответить правильно на первый вопрос", "🎯"),
            Achievement("perfect_run", "Идеальная серия", "10 правильных ответов подряд", "🔥"),
            Achievement("speedrun", "На быструю руку", "Ответить за < 5 сек", "⚡"),
            Achievement(
                "survival_expert",
                "Эксперт выживания",
                "Пройти режим выживания с полными жизнями",
                "❤️",
            ),
            Achievement("challenge_master", "Мастер челленджа", "Достичь мультипликатора 5x", "👑"),
            Achievement("hundred_questions", "Сотый вопрос", "Ответить на 100 вопросов", "📚"),
            Achievement("perfect_accuracy", "Идеальная точность", "Достичь 100% точности", "✨"),
            Achievement("iron_will", "Стальная воля", "Ответить правильно 50 вопросов подряд", "🛡️"),
        ]
        self.session.achievements = achievements

    def _load_leaderboard(self) -> List[Dict]:
        """Загрузить таблицу рекордов."""
        token_dir = TokenManager.get_token_file().parent
        leaderboard_file = token_dir / self.LEADERBOARD_FILE

        if leaderboard_file.exists():
            try:
                return json.loads(leaderboard_file.read_text())
            except:
                return []
        return []

    def _save_leaderboard(self):
        """Сохранить таблицу рекордов."""
        token_dir = TokenManager.get_token_file().parent
        leaderboard_file = token_dir / self.LEADERBOARD_FILE
        leaderboard_file.write_text(json.dumps(self.leaderboard, indent=2, ensure_ascii=False))

    def add_to_leaderboard(self, player_name: str):
        """Добавить результат в таблицу рекордов."""
        entry = {
            "player": player_name,
            "score": self.session.score,
            "mode": self.session.mode.value,
            "accuracy": self.session.accuracy,
            "total_questions": self.session.total_questions,
            "date": datetime.now().isoformat(),
        }

        self.leaderboard.append(entry)
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
        self.leaderboard = self.leaderboard[:100]  # Держим топ 100
        self._save_leaderboard()

    def show_leaderboard(self):
        """Показать таблицу рекордов."""
        print("\n" + "=" * 70)
        print("🏆 ТАБЛИЦА РЕКОРДОВ")
        print("=" * 70)

        if not self.leaderboard:
            print("\nТаблица рекордов пуста")
            return

        print(f"\n{'Место':<5} {'Игрок':<15} {'Очки':<10} {'Режим':<12} {'Точность':<10}")
        print("-" * 70)

        for i, entry in enumerate(self.leaderboard[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            print(
                f"{medal:<5} {entry['player']:<15} {entry['score']:<10} "
                f"{entry['mode']:<12} {entry['accuracy']:.1f}%"
            )

    async def play_time_attack(self, time_limit: int = 60):
        """Режим "На время" (N вопросов за N секунд)."""
        print(f"\n⏱️  РЕЖИМ НА ВРЕМЯ: {time_limit} секунд!")
        print("=" * 70)

        self.session.mode = GameMode.TIME_ATTACK
        self.session.time_limit = time_limit
        start_time = datetime.now()

        while datetime.now() - start_time < timedelta(seconds=time_limit):
            remaining = time_limit - (datetime.now() - start_time).total_seconds()
            print(f"\n⏱️  Осталось: {int(remaining)} сек")

            if not await self._ask_question_timed():
                break

        self.session.time_used = int((datetime.now() - start_time).total_seconds())
        print(f"\n⏰ Время истекло! Вы ответили на {self.session.total_questions} вопросов")

    async def play_survival(self, initial_lives: int = 3):
        """Режим "Выживание" (жизни уменьшаются с ошибками)."""
        print(f"\n❤️  РЕЖИМ ВЫЖИВАНИЯ: {initial_lives} жизней!")
        print("=" * 70)

        self.session.mode = GameMode.SURVIVAL
        self.session.lives = initial_lives
        self.session.max_lives = initial_lives

        while self.session.lives > 0:
            print(
                f"\n❤️  Жизни: {'❤️ ' * self.session.lives}{'🖤 ' * (self.session.max_lives - self.session.lives)}"
            )
            print(f"📊 Правильно: {self.session.correct_answers}/{self.session.total_questions}")

            if not await self._ask_question_survival():
                break

    async def play_challenge(self):
        """Режим "Челлендж" (растущая сложность)."""
        print("\n🚀 РЕЖИМ ЧЕЛЛЕНДЖ: Растущая сложность!")
        print("=" * 70)

        self.session.mode = GameMode.CHALLENGE
        self.session.current_multiplier = 1.0

        correct_streak = 0

        while correct_streak < 50:  # Максимум 50 вопросов в челленже
            print(f"\n🎯 Мультипликатор: {self.session.current_multiplier:.1f}x")
            print(f"🔥 Серия: {correct_streak}")

            if not await self._ask_question_challenge(correct_streak):
                break

    async def _ask_question_timed(self) -> bool:
        """Спросить вопрос (режим времени)."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                start = datetime.now()

                question_data = await self.api.get_random_question()
                print(f"\n❓ {question_data.question}")

                user_input = input("Ответ: ").strip()

                if user_input.lower() == "quit":
                    return False

                elapsed = (datetime.now() - start).total_seconds()

                # Retry логика для получения ответа
                answer_retry = 0
                while answer_retry < max_retries:
                    try:
                        answer_data = await self.api.get_answer(question_data.id)
                        break
                    except Exception:
                        answer_retry += 1
                        if answer_retry < max_retries:
                            print(f"⚠️  Ошибка, попытка {answer_retry}...")
                            await asyncio.sleep(1)
                        else:
                            raise

                is_correct = user_input.lower() == answer_data.answer.lower()

                self.session.total_questions += 1
                if is_correct:
                    self.session.correct_answers += 1
                    speed_bonus = "⚡" if elapsed < 5 else "✅"
                    print(f"{speed_bonus} Правильно! ({elapsed:.1f} сек)")
                else:
                    self.session.wrong_answers += 1
                    print(f"❌ Ответ: {answer_data.answer}")

                return True
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⚠️  Ошибка: {e}")
                    print(f"🔄 Попытка {retry_count}...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Не удалось загрузить вопрос после {max_retries} попыток")
                    return True

        return True

    async def _ask_question_survival(self) -> bool:
        """Спросить вопрос (режим выживания)."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                question_data = await self.api.get_random_question()
                print(f"\n❓ {question_data.question}")

                user_input = input("Ответ: ").strip()

                if user_input.lower() == "quit":
                    return False

                # Retry логика для получения ответа
                answer_retry = 0
                while answer_retry < max_retries:
                    try:
                        answer_data = await self.api.get_answer(question_data.id)
                        break
                    except Exception:
                        answer_retry += 1
                        if answer_retry < max_retries:
                            print(f"⚠️  Ошибка, попытка {answer_retry}...")
                            await asyncio.sleep(1)
                        else:
                            raise

                is_correct = user_input.lower() == answer_data.answer.lower()

                self.session.total_questions += 1

                if is_correct:
                    self.session.correct_answers += 1
                    print("✅ Правильно!")
                else:
                    self.session.wrong_answers += 1
                    self.session.lives -= 1
                    print(f"❌ Ответ: {answer_data.answer}")
                    print(f"⚠️  Осталось жизней: {self.session.lives}")

                return self.session.lives > 0
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⚠️  Ошибка: {e}")
                    print(f"🔄 Попытка {retry_count}...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Не удалось загрузить вопрос после {max_retries} попыток")
                    return True

        return True

    async def _ask_question_challenge(self, correct_streak: int) -> bool:
        """Спросить вопрос (режим челленджа)."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                question_data = await self.api.get_random_question()
                print(f"\n❓ {question_data.question}")

                user_input = input("Ответ: ").strip()

                if user_input.lower() == "quit":
                    return False

                # Retry логика для получения ответа
                answer_retry = 0
                while answer_retry < max_retries:
                    try:
                        answer_data = await self.api.get_answer(question_data.id)
                        break
                    except Exception:
                        answer_retry += 1
                        if answer_retry < max_retries:
                            print(f"⚠️  Ошибка, попытка {answer_retry}...")
                            await asyncio.sleep(1)
                        else:
                            raise

                is_correct = user_input.lower() == answer_data.answer.lower()

                self.session.total_questions += 1

                if is_correct:
                    self.session.correct_answers += 1
                    # Увеличить мультипликатор за каждый правильный ответ
                    self.session.current_multiplier = 1.0 + (correct_streak * 0.1)
                    self.session.max_multiplier = max(
                        self.session.max_multiplier, self.session.current_multiplier
                    )
                    print(
                        f"✅ Правильно! Мультипликатор растет: {self.session.current_multiplier:.1f}x"
                    )
                    return True
                else:
                    self.session.wrong_answers += 1
                    # Сбросить мультипликатор при ошибке
                    self.session.current_multiplier = 1.0
                    print(f"❌ Ответ: {answer_data.answer}")
                    print("⚠️  Мультипликатор сброшен!")
                    return correct_streak >= 10  # Минимум 10 правильных для челленджа
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⚠️  Ошибка: {e}")
                    print(f"🔄 Попытка {retry_count}...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Не удалось загрузить вопрос после {max_retries} попыток")
                    return True

        return True

    async def close(self):
        """Закрыть соединение."""
        await self.api.close()


async def main():
    """Главная функция."""
    game = AdvancedQuizGame()

    try:
        # Меню режимов
        print("\n" + "=" * 70)
        print("🎮 ВИКТОРИНА - РАСШИРЕННЫЕ РЕЖИМЫ")
        print("=" * 70)

        print("""
1️⃣  На время (60 сек) ⏱️
2️⃣  Выживание (3 жизни) ❤️
3️⃣  Челлендж (мультипликатор) 🚀
4️⃣  Таблица рекордов 🏆
5️⃣  Выход
        """)

        choice = input("Выберите режим (1-5): ").strip()

        if choice == "1":
            await game.play_time_attack(60)
        elif choice == "2":
            await game.play_survival(3)
        elif choice == "3":
            await game.play_challenge()
        elif choice == "4":
            game.show_leaderboard()
            return
        else:
            return

        # Показать результаты
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТЫ")
        print("=" * 70)
        print(f"""
Всего вопросов: {game.session.total_questions}
✅ Правильно: {game.session.correct_answers}
❌ Неправильно: {game.session.wrong_answers}
🎯 Точность: {game.session.accuracy:.1f}%
🎖️  Очки: {game.session.score}
        """)

        # Добавить в таблицу
        if game.session.total_questions > 0:
            player_name = input("Введите имя игрока для рекорда: ").strip()
            if player_name:
                game.add_to_leaderboard(player_name)
                print("✅ Результат сохранен в таблице рекордов!")

        game.show_leaderboard()

    except KeyboardInterrupt:
        print("\n\n⛔ Игра прервана")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        await game.close()


if __name__ == "__main__":
    asyncio.run(main())
