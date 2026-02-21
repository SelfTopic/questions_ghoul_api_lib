"""Main API session class for Questions Ghoul Quiz."""

from typing import Optional

from ghoul_quiz.client import GhoulAPIClient
from ghoul_quiz.models import (
    AnswerResponse,
    QuestionOption,
    RegistrationResponse,
    TemporaryTokenResponse,
    VerifyCodeResponse,
)


class GhoulQuizAPI:
    """High-level async API for Questions Ghoul Quiz."""

    def __init__(
        self,
        base_url: str = "http://chestor.site:3300",
        api_key: Optional[str] = None,
    ):
        """
        Initialize GhoulQuizAPI session.

        Args:
            base_url: Base URL of the API
            api_key: JWT or temporary access token (optional)
        """
        self.client = GhoulAPIClient(base_url=base_url, token=api_key)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Authentication endpoints

    async def get_temporary_token(self) -> TemporaryTokenResponse:
        """
        Get a temporary access token for guests.

        Rate Limit: 1 request/hour (per email or IP)

        Returns:
            TemporaryTokenResponse with access_token and expires_in

        Raises:
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        response = await self.client.get("/api/access_token")
        return TemporaryTokenResponse(
            access_token=response["accessToken"],
            expires_in=response["expires_in"],
        )

    async def register(self, email: str) -> RegistrationResponse:
        """
        Register a new user (send verification code to email).

        Rate Limit: 10 requests/hour

        Args:
            email: User email address

        Returns:
            RegistrationResponse with confirmation message

        Raises:
            ValidationError: If email is invalid
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        response = await self.client.post(
            "/api/register",
            json={"email": email},
        )
        return RegistrationResponse(message=response["message"])

    async def verify_code(self, email: str, code: str) -> VerifyCodeResponse:
        """
        Verify code and get JWT token.

        Rate Limit: 3 attempts/hour

        Args:
            email: User email address
            code: Verification code sent to email

        Returns:
            VerifyCodeResponse with JWT token

        Raises:
            ValidationError: If email or code is invalid
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        response = await self.client.post(
            "/api/verify-code",
            json={"email": email, "code": code},
        )
        return VerifyCodeResponse(token=response["token"])

    async def register_interactive(self, email: str, save_token: bool = True) -> str:
        """
        Complete registration flow in one step (register + verify + optionally save).

        Similar to telethon/pyrogram - handles entire registration process
        by prompting user for verification code in console.

        Args:
            email: User email address
            save_token: Whether to save token to local storage (default: True)

        Returns:
            JWT token as string

        Raises:
            ValidationError: If email is invalid
            RateLimitError: If rate limit exceeded
            APIError: For other API errors

        Example:
            api = GhoulQuizAPI()
            token = await api.register_interactive("user@example.com")
            # You will be prompted to enter verification code
            # Token will be automatically saved
            # Ready to use: question = await api.get_random_question()

        Note:
            This is a blocking call that waits for user input in the console.
            Similar to how telethon and pyrogram handle authentication.
        """
        import asyncio

        print(f"\n📧 Registering {email}...")

        # Step 1: Send verification code
        try:
            reg_response = await self.register(email=email)
            print(f"✅ {reg_response.message}")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            raise

        # Step 2: Get code from user
        print("📨 Check your email for the verification code")

        def get_code_sync() -> str:
            """Get code from console (blocking)."""
            while True:
                try:
                    code = input("🔐 Enter verification code: ").strip()
                    if not code:
                        print("❌ Code cannot be empty")
                        continue
                    if not code.isdigit():
                        print("❌ Code must contain only digits")
                        continue
                    return code
                except KeyboardInterrupt:
                    print("\n⚠️  Registration cancelled")
                    raise

        # Run sync input in executor to not block event loop
        loop = asyncio.get_event_loop()
        code = await loop.run_in_executor(None, get_code_sync)

        # Step 3: Verify code
        print("🔄 Verifying code...")
        try:
            verify_response = await self.verify_code(email=email, code=code)
            token = verify_response.token
            print("✅ Verification successful!")
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            raise

        # Step 4: Set token for immediate use
        self.set_token(token)

        # Step 5: Optionally save token
        if save_token:
            self.save_token(email)
            print(f"💾 Token saved for {email}")

        print("🎉 Registration complete! Ready to use API.\n")
        return token

    # Quiz endpoints

    async def get_random_question(self) -> QuestionOption:
        """
        Get a random question from the quiz.

        Rate Limit:
            - Temporary token: 10 requests/hour
            - JWT token: 1000 requests/hour

        Returns:
            QuestionOption with question and answer options

        Raises:
            UnauthorizedError: If token is missing or invalid
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        if not self.client.token:
            raise ValueError("Token is required. Use get_temporary_token() or verify_code() first.")

        response = await self.client.get("/api/quiz/random")
        return QuestionOption(
            id=response["id"],
            question=response["question"],
            answer_options=response["answer_options"],
            answer_group=response["answer_group"],
        )

    async def get_answer(
        self, question_id: Optional[int] = None, question_text: Optional[str] = None
    ) -> AnswerResponse:
        """
        Get the answer to a question by ID or question text.

        Rate Limit: 1000 requests/hour (JWT only)

        Args:
            question_id: Question ID
            question_text: Question text (alternative to ID)

        Returns:
            AnswerResponse with the answer

        Raises:
            ValidationError: If neither ID nor question text provided
            UnauthorizedError: If JWT token is required and missing
            NotFoundError: If question not found
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        if question_id is None and question_text is None:
            raise ValueError("Either question_id or question_text must be provided")

        if question_id is not None and question_text is not None:
            raise ValueError("Provide only one of question_id or question_text")

        payload = {}
        if question_id is not None:
            payload["id"] = question_id
        if question_text is not None:
            payload["question"] = question_text

        response = await self.client.post("/api/quiz/answer", json=payload)
        return AnswerResponse(
            id=response["id"],
            question=response["question"],
            answer=response["answer"],
            answer_group=response["answer_group"],
        )

    def set_token(self, token: str) -> None:
        """
        Set or update the authentication token.

        Args:
            token: JWT or temporary access token
        """
        self.client.token = token

    def get_token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.client.token

    def load_saved_token(self, email: str) -> bool:
        """
        Load saved JWT token from local storage.

        Args:
            email: User email address

        Returns:
            True if token was loaded successfully, False otherwise

        Example:
            api = GhoulQuizAPI()
            if api.load_saved_token("user@example.com"):
                question = await api.get_random_question()
            else:
                print("No saved token for this email")
        """
        from ghoul_quiz.register import TokenManager

        token = TokenManager.load_token(email)
        if token:
            self.set_token(token)
            return True
        return False

    def save_token(self, email: str) -> bool:
        """
        Save current token to local storage.

        Args:
            email: User email address

        Returns:
            True if token was saved successfully, False if no token is set

        Example:
            api = GhoulQuizAPI()
            token = await api.verify_code("user@example.com", "123456")
            api.save_token("user@example.com")
        """
        from ghoul_quiz.register import TokenManager

        if self.client.token:
            TokenManager.save_token(email, self.client.token)
            return True
        return False
