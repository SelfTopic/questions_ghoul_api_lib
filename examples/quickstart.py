#!/usr/bin/env python3
"""
Quick start: Register and start using the API in 3 lines

This is the easiest way to get started with Ghoul Quiz API.
"""

import asyncio

from ghoul_quiz import GhoulQuizAPI


async def main():
    """Quick start example."""

    api = GhoulQuizAPI()

    # 1. Register interactively (one line!)
    token = await api.register_interactive(email="example@example.com")

    # 2. Get a question (token is already set)
    question = await api.get_random_question()
    print(f"\n📝 Question: {question.question}")
    print(f"   Options: {', '.join(question.answer_options)}\n")

    # 3. Get the answer
    answer = await api.get_answer(question_id=question.id)
    print(f"✅ Answer: {answer.answer}\n")

    await api.close()


if __name__ == "__main__":
    asyncio.run(main())
