"""Demo of the Ghoul Quiz API: guest access, then a user session."""

import asyncio

from ghoul_quiz import AuthenticationRequiredError, GhoulQuizAPI, GhoulQuizError


async def main():
    async with GhoulQuizAPI() as api:
        try:
            print("Server healthy:", await api.health())

            # Guests: 10 questions per hour, no answers
            guest = await api.get_temporary_token()
            print(f"✓ Guest token for {guest.expires_in // 60} min")

            question = await api.get_random_question()
            print(f"✓ Question #{question.id}: {question.question}")
            print(f"✓ Options: {question.answer_options}\n")

            try:
                await api.get_answer(question_id=question.id)
            except AuthenticationRequiredError:
                print("✓ Answers need a registered user\n")

            # Users: log in by email code; the session is saved and refreshed automatically
            email = input("Email to log in (empty to skip): ").strip()
            if not email:
                return
            if not api.load_saved_token(email):
                await api.register_interactive(email)

            answer = await api.get_answer(question_id=question.id)
            print(f"✓ Answer: {answer.answer} ({answer.answer_group})")

        except GhoulQuizError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
