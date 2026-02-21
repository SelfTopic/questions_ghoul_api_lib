#!/usr/bin/env python3
"""
Interactive registration and JWT token retrieval for Ghoul Quiz API.

This module provides:
- User registration with email verification
- JWT and temporary token management
- Token storage and retrieval
- Interactive console interface

Usage:
    from ghoul_quiz.register import main
    asyncio.run(main())

    Or from command line:
    python -m ghoul_quiz.register [--api-url http://chestor.site:3300]
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from ghoul_quiz.client import RateLimitError, ValidationError
from ghoul_quiz.session import GhoulQuizAPI


class TokenManager:
    """Manage storing and retrieving JWT tokens locally.

    Token storage location is determined automatically:

    1. **Environment Variable** (highest priority)
       - Set GHOUL_QUIZ_TOKEN_PATH to override location
       - Example: export GHOUL_QUIZ_TOKEN_PATH=/custom/path/tokens.json

    2. **Development Mode** (when in project directory)
       - If setup.py or pyproject.toml exists in current directory
       - Location: ./.ghoul_quiz/tokens.json
       - Useful for development without polluting home directory

    3. **Production Mode** (default)
       - Used when not in project directory
       - Location: ~/.ghoul_quiz/tokens.json
       - Standard location for user application data

    Examples:
        >>> # Auto-detect storage location
        >>> token_file = TokenManager.get_token_file()
        >>>
        >>> # Save a token
        >>> TokenManager.save_token("user@example.com", "eyJ...", "http://api.url")
        >>>
        >>> # Load all tokens
        >>> tokens = TokenManager.load_all_tokens()
        >>>
        >>> # Load specific token
        >>> token = TokenManager.load_token("user@example.com")
        >>>
        >>> # Delete token
        >>> TokenManager.delete_token("user@example.com")
    """

    # Default locations for different environments:
    # - Production: ~/.ghoul_quiz/tokens.json (home directory)
    # - Development: ./.ghoul_quiz/tokens.json (current directory)
    #
    # Can be overridden via environment variable:
    # export GHOUL_QUIZ_TOKEN_PATH=/path/to/tokens.json

    @classmethod
    def _get_token_file(cls) -> Path:
        """Get token file path (configurable via env var)."""
        import os

        # Check for environment variable first
        custom_path = os.environ.get("GHOUL_QUIZ_TOKEN_PATH")
        if custom_path:
            return Path(custom_path)

        # Check if we're in development (has setup.py or pyproject.toml nearby)
        current_dir = Path.cwd()
        if (current_dir / "setup.py").exists() or (current_dir / "pyproject.toml").exists():
            # Development mode - use local .ghoul_quiz/
            return current_dir / ".ghoul_quiz" / "tokens.json"

        # Production mode - use home directory
        return Path.home() / ".ghoul_quiz" / "tokens.json"

    @property
    def TOKEN_FILE(self) -> Path:
        """Get token file path."""
        return self._get_token_file()

    # For backward compatibility, keep class-level access
    @classmethod
    def get_token_file(cls) -> Path:
        """Get token file path."""
        return cls._get_token_file()

    @classmethod
    def _ensure_dir(cls):
        """Create token directory if it doesn't exist."""
        token_file = cls.get_token_file()
        token_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def save_token(cls, email: str, token: str, api_url: str = "http://chestor.site:3300"):
        """Save JWT token with metadata."""
        cls._ensure_dir()

        # Load existing tokens
        tokens = cls.load_all_tokens()

        # Save new token
        tokens[email] = {
            "token": token,
            "api_url": api_url,
        }

        token_file = cls.get_token_file()
        with open(token_file, "w") as f:
            json.dump(tokens, f, indent=2)

        print(f"✅ Токен сохранен для {email}")

    @classmethod
    def load_token(cls, email: str) -> Optional[str]:
        """Load JWT token for email."""
        tokens = cls.load_all_tokens()
        if email in tokens:
            return tokens[email].get("token")
        return None

    @classmethod
    def load_all_tokens(cls) -> dict:
        """Load all saved tokens."""
        cls._ensure_dir()
        token_file = cls.get_token_file()
        if token_file.exists():
            with open(token_file, "r") as f:
                return json.load(f)
        return {}

    @classmethod
    def delete_token(cls, email: str):
        """Delete token for email."""
        tokens = cls.load_all_tokens()
        if email in tokens:
            del tokens[email]
            token_file = cls.get_token_file()
            with open(token_file, "w") as f:
                json.dump(tokens, f, indent=2)
            print(f"✅ Токен удален для {email}")

    @classmethod
    def get_token_api_url(cls, email: str) -> Optional[str]:
        """Get API URL for stored token."""
        tokens = cls.load_all_tokens()
        if email in tokens:
            return tokens[email].get("api_url")
        return None


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def get_email() -> str:
    """Get email from user with validation."""
    while True:
        email = input("\n📧 Введите ваш email: ").strip()

        if not email:
            print("❌ Email не может быть пустым")
            continue

        if "@" not in email or "." not in email:
            print("❌ Некорректный формат email")
            continue

        return email


def get_verification_code() -> str:
    """Get verification code from user."""
    while True:
        code = input("\n🔐 Введите код верификации из письма: ").strip()

        if not code:
            print("❌ Код не может быть пустым")
            continue

        if not code.isdigit() or len(code) < 4:
            print("❌ Код должен содержать минимум 4 цифры")
            continue

        return code


async def register_new_user(api: GhoulQuizAPI, email: str) -> Optional[str]:
    """Register new user and get JWT token."""
    print_header("📝 Регистрация нового пользователя")

    # Step 1: Send registration email
    print(f"\n1️⃣  Отправляю код на {email}...")
    try:
        response = await api.register(email=email)
        print(f"✅ {response.message}")
    except RateLimitError:
        print("❌ Слишком много попыток. Попробуйте позже.")
        return None
    except ValidationError as e:
        print(f"❌ Ошибка валидации: {e.message}")
        if e.details:
            print(f"   Детали: {e.details}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

    # Step 2: Get verification code
    print("\n2️⃣  Проверьте свою почту и введите код верификации")
    code = get_verification_code()

    # Step 3: Verify code and get JWT
    print("\n3️⃣  Верифицирую код...")
    try:
        verify_response = await api.verify_code(email=email, code=code)
        print("✅ Код верифицирован успешно!")
        print("\n🎉 Вы зарегистрированы и авторизованы!")

        return verify_response.token

    except ValidationError as e:
        print(f"❌ Ошибка валидации: {e.message}")
        return None
    except RateLimitError:
        print("❌ Слишком много попыток верификации. Попробуйте позже.")
        return None
    except Exception as e:
        print(f"❌ Ошибка верификации: {e}")
        return None


async def get_temporary_token_flow(api: GhoulQuizAPI) -> Optional[str]:
    """Get temporary token for guest."""
    print_header("🎫 Получение временного токена для гостя")

    try:
        print("\n⏳ Получаю временный токен...")
        response = await api.get_temporary_token()

        print("✅ Токен получен успешно!")
        print(f"   Токен: {response.access_token}")
        print(
            f"   Действителен: {response.expires_in} секунд ({response.expires_in // 3600} часов)"
        )

        return response.access_token

    except RateLimitError:
        print("❌ Лимит запросов превышен. Попробуйте позже.")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


async def use_saved_token(api: GhoulQuizAPI, token: str, api_url: str):
    """Use saved token to get and display a question."""
    print_header("✅ Использование сохраненного токена")

    api_instance = GhoulQuizAPI(base_url=api_url, api_key=token)

    try:
        print("\n⏳ Получаю вопрос с сохраненным токеном...")
        question = await api_instance.get_random_question()

        print("✅ Токен работает!")
        print("\n📝 Вопрос:")
        print(f"   ID: {question.id}")
        print(f"   Вопрос: {question.question}")
        print(f"   Варианты ответа: {', '.join(question.answer_options[:2])}...")

        # Also get the answer
        print("\n⏳ Получаю ответ...")
        answer = await api_instance.get_answer(question_id=question.id)
        print(f"✅ Ответ: {answer.answer}")

        return True

    except Exception as e:
        print(f"❌ Ошибка при использовании токена: {e}")
        return False

    finally:
        await api_instance.close()


async def test_token(api: GhoulQuizAPI, token: str) -> bool:
    """Test token by getting a question."""
    print_header("🧪 Тестирование токена")

    api.set_token(token)

    try:
        print("\n⏳ Получаю тестовый вопрос...")
        question = await api.get_random_question()

        print("✅ Токен работает!")
        print("\n📝 Тестовый вопрос:")
        print(f"   ID: {question.id}")
        print(f"   Вопрос: {question.question}")
        print(f"   Варианты ответа: {', '.join(question.answer_options[:2])}...")

        return True

    except Exception as e:
        print(f"❌ Ошибка при использовании токена: {e}")
        return False


async def show_saved_tokens():
    """Show all saved tokens."""
    print_header("💾 Сохраненные токены")

    tokens = TokenManager.load_all_tokens()

    if not tokens:
        print("\n❌ Нет сохраненных токенов")
        return

    print(f"\n✅ Найдено {len(tokens)} токен(ов):\n")

    for idx, (email, data) in enumerate(tokens.items(), 1):
        api_url = data.get("api_url", "unknown")
        token_preview = data.get("token", "")[:20] + "..."
        print(f"{idx}. Email: {email}")
        print(f"   API URL: {api_url}")
        print(f"   Token: {token_preview}")
        print()


def delete_saved_token():
    """Delete saved token."""
    print_header("🗑️  Удаление сохраненного токена")

    tokens = TokenManager.load_all_tokens()

    if not tokens:
        print("\n❌ Нет сохраненных токенов")
        return

    print("\n📧 Выберите токен для удаления:\n")

    emails = list(tokens.keys())
    for idx, email in enumerate(emails, 1):
        print(f"{idx}. {email}")

    while True:
        choice = input("\nВведите номер (или 'q' для выхода): ").strip()

        if choice.lower() == "q":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(emails):
                email = emails[idx]
                TokenManager.delete_token(email)
                return
        except ValueError:
            pass

        print("❌ Некорректный выбор")


async def use_token_interactive(api: GhoulQuizAPI):
    """Use a saved token interactively."""
    print_header("🔑 Использование сохраненного токена")

    tokens = TokenManager.load_all_tokens()

    if not tokens:
        print("\n❌ Нет сохраненных токенов")
        return

    print("\n📧 Выберите токен:\n")

    emails = list(tokens.keys())
    for idx, email in enumerate(emails, 1):
        print(f"{idx}. {email}")

    while True:
        choice = input("\nВведите номер (или 'q' для выхода): ").strip()

        if choice.lower() == "q":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(emails):
                email = emails[idx]
                token = tokens[email]["token"]
                api_url = tokens[email].get("api_url", "http://localhost:3000")

                await use_saved_token(api, token, api_url)
                return
        except ValueError:
            pass

        print("❌ Некорректный выбор")


def show_main_menu():
    """Show main menu."""
    print_header("🎯 Ghoul Quiz - Регистрация и использование токенов")

    print(
        """
1. 📝 Зарегистрировать нового пользователя и получить JWT
2. 🎫 Получить временный токен для гостя
3. 🔑 Использовать сохраненный токен
4. 💾 Просмотреть сохраненные токены
5. 🗑️  Удалить сохраненный токен
6. ❌ Выход
    """
    )


async def main():
    """Main async function."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Ghoul Quiz registration")
    parser.add_argument(
        "--api-url",
        default="http://localhost:3000",
        help="API URL (default: http://localhost:3000)",
    )
    parser.add_argument("--email", help="Email for auto-registration (skip interactive mode)")
    args = parser.parse_args()

    api = GhoulQuizAPI(base_url=args.api_url)

    try:
        # Auto-registration mode
        if args.email:
            print_header("🚀 Режим автоматической регистрации")
            print(f"\nEmail: {args.email}")
            print(f"API URL: {args.api_url}")

            token = await register_new_user(api, args.email)

            if token:
                # Test token
                if await test_token(api, token):
                    # Ask to save
                    save = input("\n💾 Сохранить токен? (y/n): ").strip().lower()
                    if save == "y":
                        TokenManager.save_token(args.email, token, args.api_url)
            return

        # Interactive mode
        while True:
            show_main_menu()
            choice = input("Выберите пункт (1-6): ").strip()

            if choice == "1":
                # Register new user
                email = get_email()

                # Check if already registered
                saved_token = TokenManager.load_token(email)
                if saved_token:
                    use_saved = (
                        input(
                            f"\n✅ Найден сохраненный токен для {email}. Использовать его? (y/n): "
                        )
                        .strip()
                        .lower()
                    )
                    if use_saved == "y":
                        api_url = TokenManager.get_token_api_url(email) or args.api_url
                        await use_saved_token(api, saved_token, api_url)
                        continue

                token = await register_new_user(api, email)

                if token:
                    # Test token
                    if await test_token(api, token):
                        # Ask to save
                        save = input("\n💾 Сохранить токен? (y/n): ").strip().lower()
                        if save == "y":
                            TokenManager.save_token(email, token, args.api_url)

            elif choice == "2":
                # Get temporary token
                token = await get_temporary_token_flow(api)

                if token:
                    if await test_token(api, token):
                        print("\n💡 Совет: Используйте эту библиотеку в своем коде:")
                        print(
                            """
    from ghoul_quiz import GhoulQuizAPI
    import asyncio
    
    async def main():
        api = GhoulQuizAPI()
        question = await api.get_random_question()
                        """
                        )

            elif choice == "3":
                # Use saved token
                await use_token_interactive(api)

            elif choice == "4":
                # Show saved tokens
                await show_saved_tokens()

            elif choice == "5":
                # Delete token
                delete_saved_token()

            elif choice == "6":
                # Exit
                print("\n👋 До свидания!\n")
                break

            else:
                print("❌ Некорректный выбор")

    finally:
        await api.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
