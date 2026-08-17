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
    def test_generate_response_uses_groq_configuration(self):
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="llama-3.3-70b-versatile",
            MAX_TOKENS=500,
            TEMPERATURE=0.2,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient()) as mock_groq:
                service = LLMService()
                response = service.generate_response("Customer asked for a quote.")

                call = mock_groq.return_value.chat.completions.kwargs
                self.assertEqual(call["model"], "llama-3.3-70b-versatile")
                self.assertEqual(call["max_tokens"], 500)
                self.assertEqual(call["temperature"], 0.2)
                self.assertEqual(response, "Polished reply")


if __name__ == "__main__":
    unittest.main()
