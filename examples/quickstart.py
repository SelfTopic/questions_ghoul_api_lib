#!/usr/bin/env python3
"""
Quick start: log in once, then the session is reused and refreshed automatically.

The first run asks for the code sent to your email; later runs load the saved
session (valid for 30 days since the last use).
"""

import asyncio

from ghoul_quiz import GhoulQuizAPI

EMAIL = "example@example.com"


async def main():
    async with GhoulQuizAPI() as api:
        # 1. Log in: saved session or code from the email
        if not api.load_saved_token(EMAIL):
            await api.register_interactive(EMAIL)

        # 2. Get a question
        question = await api.get_random_question()
        print(f"\n📝 Question: {question.question}")
        print(f"   Options: {', '.join(question.answer_options)}\n")

        # 3. Get the answer (registered users only)
        answer = await api.get_answer(question_id=question.id)
        print(f"✅ Answer: {answer.answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
