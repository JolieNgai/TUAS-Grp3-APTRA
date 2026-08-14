import unittest
from unittest.mock import patch

from flask import Flask

from app.services.llm_service import LLMService


class DummyMessage:
    content = "Polished reply"


class DummyChoice:
    message = DummyMessage()


class DummyCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("DummyResponse", (), {"choices": [DummyChoice()]})()


class DummyClient:
    def __init__(self):
        self.chat = type("DummyChat", (), {"completions": DummyCompletions()})()


class LLMServiceTest(unittest.TestCase):
    def test_generate_response_uses_requested_length_limits(self):
        app = Flask(__name__)
        app.config.update(
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="test-key",
            OPENAI_MODEL="gpt-4o-mini",
            MAX_TOKENS=500,
            TEMPERATURE=0.2,
        )

        with app.app_context():
            with patch("openai.OpenAI", return_value=DummyClient()) as mock_openai:
                service = LLMService()
                service.generate_response("Customer asked for a quote.", "friendly", "short")
                short_call = mock_openai.return_value.chat.completions.kwargs
                self.assertEqual(short_call["max_tokens"], 25)

                service.generate_response("Customer asked for a quote.", "friendly", "medium")
                medium_call = mock_openai.return_value.chat.completions.kwargs
                self.assertEqual(medium_call["max_tokens"], 50)

                service.generate_response("Customer asked for a quote.", "friendly", "long")
                long_call = mock_openai.return_value.chat.completions.kwargs
                self.assertEqual(long_call["max_tokens"], 250)


if __name__ == "__main__":
    unittest.main()
