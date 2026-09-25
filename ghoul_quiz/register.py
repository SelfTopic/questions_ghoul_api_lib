#!/usr/bin/env python3
"""
Interactive console tool for Ghoul Quiz API sessions.

- Log in / sign up by email and save the session
- Get a guest token
- Check, list and log out saved sessions

Usage:
    ghoul-quiz-register [--api-url https://chestor.site/api] [--email user@example.com]
    python -m ghoul_quiz.register
"""

import argparse
import asyncio
import sys
from datetime import datetime
from typing import List, Optional

from ghoul_quiz.errors import GhoulQuizError
from ghoul_quiz.session import GhoulQuizAPI
from ghoul_quiz.storage import DEFAULT_BASE_URL, TokenManager, normalize_url

# Kept for code that imported TokenManager from here in version 0.1.
__all__ = ["TokenManager", "main"]


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def format_ts(ts: Optional[float]) -> str:
    if not ts:
        return "неизвестно"
    moment = datetime.fromtimestamp(ts)
    suffix = " (истёк)" if moment < datetime.now() else ""
    return moment.strftime("%Y-%m-%d %H:%M") + suffix


def ask_email() -> str:
    while True:
        email = input("\n📧 Введите email: ").strip()
        if "@" in email and "." in email.split("@")[-1]:
            return email
        print("❌ Некорректный формат email")


def saved_emails(api_url: str) -> List[str]:
    return [
        email
        for email, entry in TokenManager.load_all().items()
        if normalize_url(entry.get("api_url", "")) == normalize_url(api_url)
    ]


def choose_saved_email(api_url: str) -> Optional[str]:
    emails = saved_emails(api_url)
    if not emails:
        print(f"\n❌ Нет сохранённых сессий для {api_url}")
        return None

    print()
    for idx, email in enumerate(emails, 1):
        print(f"{idx}. {email}")
    while True:
        choice = input("\nНомер (или 'q' для отмены): ").strip()
        if choice.lower() == "q":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(emails):
            return emails[int(choice) - 1]
        print("❌ Некорректный выбор")


async def show_test_question(api: GhoulQuizAPI) -> bool:
    """Request one question (and its answer for users) to check the token."""
    try:
        question = await api.get_random_question()
        print("\n✅ Токен работает")
        print(f"\n📝 Вопрос #{question.id}: {question.question}")
        print(f"   Варианты: {', '.join(question.answer_options)}")
        if api.auth_type == "user":
            answer = await api.get_answer(question_id=question.id)
            print(f"   Ответ: {answer.answer}")
        return True
    except GhoulQuizError as e:
        print(f"❌ {e}")
        return False


async def login_flow(api: GhoulQuizAPI, email: Optional[str] = None) -> None:
    print_header("📝 Вход / регистрация по email")
    email = email or ask_email()

    if api.load_saved_token(email):
        use_saved = input(f"\n✅ Есть сохранённая сессия для {email}. Использовать её? (y/n): ")
        if use_saved.strip().lower() == "y":
            await show_test_question(api)
            return

    try:
        await api.register_interactive(email, save_token=True)
    except GhoulQuizError as e:
        print(f"❌ {e}")
        return
    await show_test_question(api)


async def guest_flow(api: GhoulQuizAPI) -> None:
    print_header("🎫 Гостевой токен")
    try:
        guest = await api.get_temporary_token()
    except GhoulQuizError as e:
        print(f"❌ {e}")
        return
    print(f"\n✅ Токен: {guest.access_token}")
    print(f"   Действует {guest.expires_in // 60} мин, 10 вопросов в час, без доступа к ответам")
    await show_test_question(api)


async def check_saved_flow(api: GhoulQuizAPI) -> None:
    print_header("🔑 Проверка сохранённой сессии")
    email = choose_saved_email(api.base_url)
    if not email:
        return
    if not api.load_saved_token(email):
        print("❌ Сессия устарела и удалена, войдите заново")
        return
    await show_test_question(api)


def list_saved_flow() -> None:
    print_header("💾 Сохранённые сессии")
    print(f"\nФайл: {TokenManager.get_token_file()}")
    sessions = TokenManager.load_all()
    if not sessions:
        print("\n❌ Нет сохранённых сессий")
        return

    for email, entry in sessions.items():
        print(f"\n• {email}")
        print(f"  Сервер:            {entry.get('api_url', 'неизвестно')}")
        if entry.get("refresh_token"):
            print(f"  Access-токен до:   {format_ts(entry.get('expires_at'))}")
            print(f"  Refresh-токен до:  {format_ts(entry.get('refresh_expires_at'))}")
        else:
            print("  Старый формат без refresh-токена: нужен повторный вход")


async def logout_flow(api: GhoulQuizAPI, everywhere: bool) -> None:
    print_header("🚪 Выход на всех устройствах" if everywhere else "🚪 Выход из сессии")
    email = choose_saved_email(api.base_url)
    if not email or not api.load_saved_token(email):
        return
    try:
        if everywhere:
            await api.logout_all()
        else:
            await api.logout()
        print(f"✅ Сессия {email} завершена и удалена")
    except GhoulQuizError as e:
        print(f"❌ {e}")
        if TokenManager.delete(email):
            print("   Локальная копия удалена")


async def health_flow(api: GhoulQuizAPI) -> None:
    try:
        ok = await api.health()
    except GhoulQuizError as e:
        print(f"\n❌ Сервер недоступен: {e}")
        return
    print(f"\n{'✅ Сервер работает' if ok else '⚠️  Сервер отвечает, но БД или Redis недоступны'}")


MENU = """
1. 📝 Войти / зарегистрироваться по email
2. 🎫 Получить гостевой токен
3. 🔑 Проверить сохранённую сессию
4. 💾 Показать сохранённые сессии
5. 🚪 Выйти из сессии
6. 🚫 Выйти на всех устройствах
7. 🩺 Статус сервера
0. ❌ Выход
"""


async def run(api_url: str, email: Optional[str], verify_ssl: bool) -> None:
    async with GhoulQuizAPI(base_url=api_url, verify_ssl=verify_ssl) as api:
        if email:
            await login_flow(api, email)
            return

        while True:
            print_header(f"🎯 Ghoul Quiz: сессии ({api.base_url})")
            print(MENU)
            choice = input("Выберите пункт: ").strip()
            api.clear()

            if choice == "1":
                await login_flow(api)
            elif choice == "2":
                await guest_flow(api)
            elif choice == "3":
                await check_saved_flow(api)
            elif choice == "4":
                list_saved_flow()
            elif choice == "5":
                await logout_flow(api, everywhere=False)
            elif choice == "6":
                await logout_flow(api, everywhere=True)
            elif choice == "7":
                await health_flow(api)
            elif choice == "0":
                print("\n👋 До свидания!\n")
                return
            else:
                print("❌ Некорректный выбор")


def main() -> None:
    """Console entry point."""
    parser = argparse.ArgumentParser(description="Ghoul Quiz: вход и управление сессиями")
    parser.add_argument(
        "--api-url",
        default=DEFAULT_BASE_URL,
        help=f"корень API, включая /api (по умолчанию {DEFAULT_BASE_URL})",
    )
    parser.add_argument("--email", help="сразу войти с этим email, без меню")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="не проверять SSL-сертификат (для локального сервера)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run(args.api_url, args.email, verify_ssl=not args.insecure))
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(130)


if __name__ == "__main__":
    main()
