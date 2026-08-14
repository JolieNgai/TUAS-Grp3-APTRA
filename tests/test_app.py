import unittest
from unittest.mock import patch

from app import create_app
from app.services.llm_service import LLMService


class AppPromptGenerationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, OPENAI_API_KEY="test-key")
        self.client = self.app.test_client()

    def test_build_reply_prompt_contains_email_tone_and_length(self):
        prompt = LLMService.build_reply_prompt(
            "Hi team, I am confirming the meeting time.",
            "professional",
            "short",
        )

        self.assertIn("Hi team, I am confirming the meeting time.", prompt)
        self.assertIn("professional", prompt.lower())
        self.assertIn("short", prompt.lower())
        self.assertIn("Write a reply email", prompt)

    @patch("app.routes.LLMService.generate_response", return_value="Thank you for the update.")
    def test_post_route_generates_reply_for_frontend(self, mock_generate_response):
        response = self.client.post(
            "/",
            data={
                "prompt": "Hi team, I am confirming the meeting time.",
                "tone": "professional",
                "length": "short",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Thank you for the update.", response.get_data(as_text=True))
        mock_generate_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
