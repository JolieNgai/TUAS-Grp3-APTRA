import unittest
from unittest.mock import patch

from flask import Flask

from app.services.llm_service import LLMService


class DummyMessage:
    def __init__(self, content="Polished reply"):
        self.content = content


class DummyChoice:
    def __init__(self, content="Polished reply"):
        self.message = DummyMessage(content)


class DummyCompletions:
    def __init__(self, response_content="Polished reply"):
        self.response_content = response_content

    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("DummyResponse", (), {"choices": [DummyChoice(self.response_content)]})()


class DummyClient:
    def __init__(self, response_content="Polished reply"):
        self.chat = type("DummyChat", (), {"completions": DummyCompletions(response_content)})()


class LLMServiceBuildPromptTest(unittest.TestCase):
    """Unit tests for build_reply_prompt"""

    def test_build_reply_prompt_basic(self):
        """Test basic prompt building with all fields"""
        prompt = LLMService.build_reply_prompt(
            email_text="Hello, can you help?",
            tone="professional",
            length="medium"
        )
        self.assertIn("Hello, can you help?", prompt)
        self.assertIn("professional", prompt)
        self.assertIn("medium", prompt)
        self.assertIn("3-5 sentences", prompt)

    def test_build_reply_prompt_with_context(self):
        """Test prompt includes additional context when provided"""
        prompt = LLMService.build_reply_prompt(
            email_text="Help needed",
            tone="casual",
            length="short",
            additional_context="Please be brief"
        )
        self.assertIn("Please be brief", prompt)
        self.assertIn("Additional context", prompt)

    def test_build_reply_prompt_without_context(self):
        """Test prompt excludes context instruction when empty"""
        prompt = LLMService.build_reply_prompt(
            email_text="Help needed",
            tone="casual",
            length="short",
            additional_context=""
        )
        self.assertNotIn("Additional context", prompt)

    def test_build_reply_prompt_tone_case_insensitivity(self):
        """Test tone is normalized to lowercase"""
        prompt_upper = LLMService.build_reply_prompt("Test", "PROFESSIONAL", "medium")
        prompt_lower = LLMService.build_reply_prompt("Test", "professional", "medium")
        # Both should produce same result
        self.assertIn("professional", prompt_upper.lower())
        self.assertIn("professional", prompt_lower.lower())

    def test_build_reply_prompt_length_short(self):
        """Test short length guidance is applied"""
        prompt = LLMService.build_reply_prompt("Test", "professional", "short")
        self.assertIn("1-2 sentences", prompt)

    def test_build_reply_prompt_length_medium(self):
        """Test medium length guidance is applied"""
        prompt = LLMService.build_reply_prompt("Test", "professional", "medium")
        self.assertIn("3-5 sentences", prompt)

    def test_build_reply_prompt_length_long(self):
        """Test long length guidance is applied"""
        prompt = LLMService.build_reply_prompt("Test", "professional", "long")
        self.assertIn("6 or more sentences", prompt)

    def test_build_reply_prompt_whitespace_handling(self):
        """Test that leading/trailing whitespace is stripped"""
        prompt = LLMService.build_reply_prompt(
            email_text="  Spaced email  ",
            tone="  professional  ",
            length="  medium  ",
            additional_context="  context  "
        )
        self.assertNotIn("  Spaced", prompt)
        self.assertIn("Spaced email", prompt)

    def test_build_reply_prompt_empty_tone_defaults_to_professional(self):
        """Test empty tone defaults to professional"""
        prompt = LLMService.build_reply_prompt("Test", "", "medium")
        self.assertIn("professional", prompt)

    def test_build_reply_prompt_empty_length_defaults_to_medium(self):
        """Test empty length defaults to medium"""
        prompt = LLMService.build_reply_prompt("Test", "professional", "")
        self.assertIn("3-5 sentences", prompt)

    def test_build_reply_prompt_unknown_length_fallback(self):
        """Test unknown length falls back to generic guidance"""
        prompt = LLMService.build_reply_prompt("Test", "professional", "unknown_length")
        self.assertIn("clear and professional", prompt)


class LLMServiceGenerationTest(unittest.TestCase):
    """Unit tests for generate_response"""

    def test_generate_response_uses_groq_configuration(self):
        """Test that generate_response passes correct Groq config"""
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="qwen/qwen3.6-27b",
            MAX_TOKENS=500,
            TEMPERATURE=0.2,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient()) as mock_groq:
                service = LLMService()
                response = service.generate_response("Customer asked for a quote.")

                mock_groq.assert_called_once_with(api_key="test-key")
                call = mock_groq.return_value.chat.completions.kwargs
                self.assertEqual(call["model"], "qwen/qwen3.6-27b")
                self.assertEqual(call["max_tokens"], 500)
                self.assertEqual(call["temperature"], 0.2)
                self.assertEqual(call["reasoning_effort"], "none")
                self.assertEqual(call["reasoning_format"], "hidden")
                self.assertEqual(response, "Polished reply")

    def test_generate_response_returns_stripped_content(self):
        """Test that response content is stripped of whitespace"""
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="qwen/qwen3.6-27b",
            MAX_TOKENS=500,
            TEMPERATURE=0.7,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient("  Spaced reply  ")):
                service = LLMService()
                response = service.generate_response("Test prompt")
                self.assertEqual(response, "Spaced reply")

    def test_generate_response_removes_reasoning_and_output_wrapper(self):
        leaked_response = (
            "- All constraints met. Proceeds.\n"
            "- Output matches response.\n"
            "- Done.\n"
            "- [Output Generation] -> \"Thanks for the reminder, Anne! "
            "I'll pack my swimsuit. See you soon!\" ("
        )
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="qwen/qwen3.6-27b",
            MAX_TOKENS=500,
            TEMPERATURE=0.7,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient(leaked_response)):
                service = LLMService()
                response = service.generate_response("Test prompt")

        self.assertEqual(
            response,
            "Thanks for the reminder, Anne! I'll pack my swimsuit. See you soon!",
        )

    def test_generate_response_removes_think_block(self):
        content = "<think>I should write a concise reply.</think>\nHere is the clean reply."
        self.assertEqual(
            LLMService.clean_generated_reply(content),
            "Here is the clean reply.",
        )

    def test_recovers_draft_when_reasoning_ends_before_final_output(self):
        content = """2. **Identify Key Points:**
- Keep it short

3. **Draft - Mental Refinement:**
Thank you for the reminder. I look forward to seeing you soon.

Check constraints:
- Short? Yes.

4. **Final Output Generation:** (Ensure strict compliance)"""
        self.assertEqual(
            LLMService.clean_generated_reply(content),
            "Thank you for the reminder. I look forward to seeing you soon.",
        )

    def test_generate_response_message_structure(self):
        """Test that messages are structured correctly"""
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="qwen/qwen3.6-27b",
            MAX_TOKENS=500,
            TEMPERATURE=0.7,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient()) as mock_groq:
                service = LLMService()
                service.generate_response("Test prompt")

                # Verify message structure
                call = mock_groq.return_value.chat.completions.kwargs
                messages = call["messages"]
                self.assertEqual(len(messages), 2)
                self.assertEqual(messages[0]["role"], "system")
                self.assertIn("email", messages[0]["content"].lower())
                self.assertEqual(messages[1]["role"], "user")
                self.assertEqual(messages[1]["content"], "Test prompt")

    def test_generate_response_missing_api_key_raises_error(self):
        """Test that missing GROQ_API_KEY raises ValueError"""
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY=None,
            GROQ_MODEL="qwen/qwen3.6-27b",
            MAX_TOKENS=500,
            TEMPERATURE=0.7,
        )

        with app.app_context():
            with self.assertRaises(ValueError) as context:
                LLMService()
            self.assertIn("GROQ_API_KEY", str(context.exception))

    def test_generate_response_custom_model_config(self):
        """Test that custom model from config is used"""
        app = Flask(__name__)
        app.config.update(
            GROQ_API_KEY="test-key",
            GROQ_MODEL="custom-model",
            MAX_TOKENS=1000,
            TEMPERATURE=0.5,
        )

        with app.app_context():
            with patch("app.services.llm_service.Groq", return_value=DummyClient()) as mock_groq:
                service = LLMService()
                service.generate_response("Test")

                call = mock_groq.return_value.chat.completions.kwargs
                self.assertEqual(call["model"], "custom-model")
                self.assertEqual(call["max_tokens"], 1000)
                self.assertEqual(call["temperature"], 0.5)


if __name__ == "__main__":
    unittest.main()
