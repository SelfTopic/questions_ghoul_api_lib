"""Demo script showing how to use Ghoul Quiz API."""

import asyncio

from ghoul_quiz import GhoulQuizAPI


async def main():
    """
    Example usage of GhoulQuizAPI.

    This demo shows how to:
    1. Get a temporary access token
    2. Get a random question
    3. Get the answer to a question
    """
    async with GhoulQuizAPI() as quiz_api:
        try:
            # Step 1: Get temporary token (for guests)
            print("Getting temporary access token...")
            token_response = await quiz_api.register_interactive("example@example.com")
            print(f"✓ Token received: {token_response[:20]}...")

            # Step 2: Get a random question
            print("Getting random question...")
            question = await quiz_api.get_random_question()
            print(f"✓ Question ID: {question.id}")
            print(f"✓ Question: {question.question}")
            print(f"✓ Options: {question.answer_options}\n")

            # Step 3: Get the answer
            print("Getting answer...")
            answer = await quiz_api.get_answer(question_id=question.id)
            print(f"✓ Answer: {answer.answer}")
            print(f"✓ Answer Group: {answer.answer_group}\n")

            # Example: You can also register and get JWT token
            # print("Registering user...")
            # await quiz_api.register(email="user@example.com")
            # print("Check your email for verification code")
            # token = await quiz_api.verify_code(email="user@example.com", code="123456")
            # quiz_api.set_token(token.token)

        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
