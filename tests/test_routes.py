import unittest
from unittest.mock import patch

from app import create_app
from app.services.llm_service import LLMService


class IndexRouteUITest(unittest.TestCase):
    """Tests for UI elements and page structure"""

    def test_index_includes_speech_controls(self):
        app = create_app()
        app.config.update(TESTING=True)

        response = app.test_client().get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-feature="speech-to-text"', html)
        self.assertIn('data-speech-target="prompt"', html)
        self.assertIn('id="speechStatus"', html)

    @patch("app.routes.LLMService")
    def test_post_keeps_selected_tone_and_length(self, mock_service):
        mock_service.return_value.generate_response.return_value = "Generated reply"
        app = create_app()
        app.config.update(TESTING=True)

        response = app.test_client().post(
            "/",
            data={"prompt": "Please send an update.", "tone": "friendly", "length": "long"},
        )
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('value="friendly" selected', html)
        self.assertIn('value="long" selected', html)
        self.assertIn("Generated reply", html)
        self.assertIn('data-speech-target="resultContent"', html)
        self.assertIn('id="resultContent"', html)
        self.assertIn('id="copyReplyButton"', html)


class IndexRouteIntegrationTest(unittest.TestCase):
    """Integration tests for successful submissions"""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("app.routes.LLMService")
    def test_valid_submission_all_fields(self, mock_service):
        """Test successful submission with all fields populated"""
        mock_service.return_value.generate_response.return_value = "Perfect reply!"

        response = self.client.post(
            "/",
            data={
                "prompt": "Can you help with this?",
                "tone": "professional",
                "length": "medium",
                "additional_context": "Be concise"
            }
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Perfect reply!", html)
        mock_service.return_value.build_reply_prompt.assert_called_once_with(
            "Can you help with this?", "professional", "medium", "Be concise"
        )
        mock_service.return_value.generate_response.assert_called_once_with(
            mock_service.return_value.build_reply_prompt.return_value
        )

    @patch("app.routes.LLMService")
    def test_valid_submission_without_context(self, mock_service):
        """Test successful submission without additional context"""
        mock_service.return_value.generate_response.return_value = "Reply generated"

        response = self.client.post(
            "/",
            data={
                "prompt": "Question here",
                "tone": "casual",
                "length": "short",
                "additional_context": ""
            }
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Reply generated", html)

    @patch("app.routes.LLMService")
    def test_all_tone_values_accepted(self, mock_service):
        """Test that all allowed tones are accepted"""
        mock_service.return_value.generate_response.return_value = "Reply"

        for tone in ["professional", "casual", "formal", "friendly", "diplomatic"]:
            response = self.client.post(
                "/",
                data={
                    "prompt": "Test email",
                    "tone": tone,
                    "length": "medium"
                }
            )
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn("Reply", html)
            self.assertNotIn("Invalid tone", html)

    @patch("app.routes.LLMService")
    def test_all_length_values_accepted(self, mock_service):
        """Test that all allowed lengths are accepted"""
        mock_service.return_value.generate_response.return_value = "Reply"

        for length in ["short", "medium", "long"]:
            response = self.client.post(
                "/",
                data={
                    "prompt": "Test email",
                    "tone": "professional",
                    "length": length
                }
            )
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn("Reply", html)
            self.assertNotIn("Invalid length", html)


class IndexRouteValidationTest(unittest.TestCase):
    """Tests for input validation logic"""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("app.routes.LLMService")
    def test_missing_prompt_shows_no_result(self, mock_service):
        """Test that missing prompt returns no result"""
        response = self.client.post(
            "/",
            data={
                "prompt": "",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Paste an email to generate a reply", html)
        mock_service.assert_not_called()

    @patch("app.routes.LLMService")
    def test_missing_tone_shows_no_result(self, mock_service):
        """Test that missing tone returns no result"""
        response = self.client.post(
            "/",
            data={
                "prompt": "Valid prompt",
                "tone": "",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Paste an email to generate a reply", html)
        mock_service.assert_not_called()

    @patch("app.routes.LLMService")
    def test_missing_length_shows_no_result(self, mock_service):
        """Test that missing length returns no result"""
        response = self.client.post(
            "/",
            data={
                "prompt": "Valid prompt",
                "tone": "professional",
                "length": ""
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Paste an email to generate a reply", html)
        mock_service.assert_not_called()

    @patch("app.routes.LLMService")
    def test_whitespace_only_prompt_ignored(self, mock_service):
        """Test that whitespace-only prompt is treated as empty"""
        response = self.client.post(
            "/",
            data={
                "prompt": "   \n\t  ",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Paste an email to generate a reply", html)
        mock_service.assert_not_called()

    def test_invalid_tone_rejected_with_message(self):
        """Test that invalid tone is rejected with appropriate message"""
        response = self.client.post(
            "/",
            data={
                "prompt": "Valid prompt",
                "tone": "aggressive",  # Not in ALLOWED_TONES
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Invalid tone selected", html)
        self.assertNotIn("aggressive", html)  # Invalid value should not appear in output

    def test_invalid_length_rejected_with_message(self):
        """Test that invalid length is rejected with appropriate message"""
        response = self.client.post(
            "/",
            data={
                "prompt": "Valid prompt",
                "tone": "professional",
                "length": "extra_long"  # Not in ALLOWED_LENGTHS
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Invalid length selected", html)

    def test_case_insensitive_tone_validation(self):
        """Test that tone validation is case-insensitive"""
        with patch("app.routes.LLMService") as mock_service:
            mock_service.return_value.generate_response.return_value = "Reply"

            # Test with uppercase
            response = self.client.post(
                "/",
                data={
                    "prompt": "Valid prompt",
                    "tone": "PROFESSIONAL",
                    "length": "medium"
                }
            )

            html = response.get_data(as_text=True)
            self.assertIn("Reply", html)
            self.assertNotIn("Invalid tone", html)

    def test_case_insensitive_length_validation(self):
        """Test that length validation is case-insensitive"""
        with patch("app.routes.LLMService") as mock_service:
            mock_service.return_value.generate_response.return_value = "Reply"

            # Test with uppercase
            response = self.client.post(
                "/",
                data={
                    "prompt": "Valid prompt",
                    "tone": "professional",
                    "length": "MEDIUM"
                }
            )

            html = response.get_data(as_text=True)
            self.assertIn("Reply", html)
            self.assertNotIn("Invalid length", html)


class IndexRouteBoundaryTest(unittest.TestCase):
    """Boundary and limit testing"""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("app.routes.LLMService")
    def test_prompt_at_max_length_accepted(self, mock_service):
        """Test that prompt at exact MAX_PROMPT_LENGTH is accepted"""
        mock_service.return_value.generate_response.return_value = "Reply"

        # Create prompt exactly 10000 characters
        long_prompt = "a" * 10000

        response = self.client.post(
            "/",
            data={
                "prompt": long_prompt,
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Reply", html)
        self.assertNotIn("too long", html)

    def test_prompt_exceeding_max_length_rejected(self):
        """Test that prompt exceeding MAX_PROMPT_LENGTH is rejected"""
        # Create prompt with 10001 characters (exceeds limit)
        long_prompt = "a" * 10001

        response = self.client.post(
            "/",
            data={
                "prompt": long_prompt,
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Input is too long", html)
        self.assertIn("10000", html)

    @patch("app.routes.LLMService")
    def test_context_at_max_length_accepted(self, mock_service):
        """Test that context at exact MAX_CONTEXT_LENGTH is accepted"""
        mock_service.return_value.generate_response.return_value = "Reply"

        # Create context exactly 5000 characters
        long_context = "c" * 5000

        response = self.client.post(
            "/",
            data={
                "prompt": "Test email",
                "tone": "professional",
                "length": "medium",
                "additional_context": long_context
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Reply", html)
        self.assertNotIn("Additional context is too long", html)

    def test_context_exceeding_max_length_rejected(self):
        """Test that context exceeding MAX_CONTEXT_LENGTH is rejected"""
        # Create context with 5001 characters (exceeds limit)
        long_context = "c" * 5001

        response = self.client.post(
            "/",
            data={
                "prompt": "Test email",
                "tone": "professional",
                "length": "medium",
                "additional_context": long_context
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Additional context is too long", html)
        self.assertIn("5000", html)

    @patch("app.routes.LLMService")
    def test_single_character_prompt_accepted(self, mock_service):
        """Test that single character prompt is accepted"""
        mock_service.return_value.generate_response.return_value = "Reply"

        response = self.client.post(
            "/",
            data={
                "prompt": "a",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("Reply", html)

    @patch("app.routes.LLMService")
    def test_surrounding_whitespace_is_removed_before_limit_check(self, mock_service):
        mock_service.return_value.generate_response.return_value = "Reply"
        response = self.client.post(
            "/",
            data={
                "prompt": " " + ("a" * 10000) + " ",
                "tone": "professional",
                "length": "medium",
                "additional_context": " " + ("c" * 5000) + " ",
            },
        )
        self.assertIn("Reply", response.get_data(as_text=True))


class IndexRouteErrorHandlingTest(unittest.TestCase):
    """Tests for error handling and recovery"""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("app.routes.LLMService")
    def test_configuration_error_shows_generic_message(self, mock_service):
        """Test that configuration errors show generic message to user"""
        mock_service.side_effect = ValueError("GROQ_API_KEY is not configured.")

        response = self.client.post(
            "/",
            data={
                "prompt": "Test email",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        # Should show generic message, not the actual error
        self.assertIn("Unable to generate a reply right now", html)
        self.assertNotIn("GROQ_API_KEY", html)
        self.assertNotIn("not configured", html)

    @patch("app.routes.LLMService")
    def test_llm_generation_error_shows_generic_message(self, mock_service):
        """Test that LLM errors show generic message to user"""
        mock_service.return_value.generate_response.side_effect = Exception("PRIVATE_RATE_LIMIT_DETAIL")

        response = self.client.post(
            "/",
            data={
                "prompt": "Test email",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        # Should show generic message, not the actual error
        self.assertIn("An error occurred while generating the reply", html)
        self.assertNotIn("PRIVATE_RATE_LIMIT_DETAIL", html)

    @patch("app.routes.LLMService")
    def test_network_error_shows_generic_message(self, mock_service):
        """Test that network errors show generic message to user"""
        mock_service.return_value.generate_response.side_effect = ConnectionError("Unable to reach API")

        response = self.client.post(
            "/",
            data={
                "prompt": "Test email",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        self.assertIn("An error occurred", html)
        self.assertNotIn("ConnectionError", html)
        self.assertNotIn("Unable to reach", html)

    @patch("app.routes.LLMService")
    def test_user_values_preserved_on_error(self, mock_service):
        """Test that user input is preserved when an error occurs"""
        mock_service.return_value.generate_response.side_effect = Exception("Error")

        response = self.client.post(
            "/",
            data={
                "prompt": "My test prompt",
                "tone": "friendly",
                "length": "long",
                "additional_context": "Please be brief"
            }
        )

        html = response.get_data(as_text=True)
        # Values should be preserved in form
        self.assertIn('>My test prompt</textarea>', html)
        self.assertIn('value="friendly" selected', html)
        self.assertIn('value="long" selected', html)
        self.assertIn('>Please be brief</textarea>', html)


class IndexRouteFeatureTest(unittest.TestCase):
    """Tests for complete feature workflows"""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("app.routes.LLMService")
    def test_complete_email_generation_workflow(self, mock_service):
        """Test complete flow from input to output"""
        mock_service.return_value.generate_response.return_value = "Thank you for your inquiry. I will get back to you soon."

        # Step 1: GET initial page
        get_response = self.client.get("/")
        self.assertEqual(get_response.status_code, 200)

        # Step 2: POST with email details
        post_response = self.client.post(
            "/",
            data={
                "prompt": "Hi, are you available tomorrow?",
                "tone": "professional",
                "length": "short"
            }
        )

        self.assertEqual(post_response.status_code, 200)
        html = post_response.get_data(as_text=True)

        # Step 3: Verify result is displayed
        self.assertIn("Thank you for your inquiry", html)

        # Step 4: Verify LLMService was called
        mock_service.return_value.build_reply_prompt.assert_called()
        mock_service.return_value.generate_response.assert_called()

    @patch("app.routes.LLMService")
    def test_response_with_special_characters(self, mock_service):
        """Test that responses with special characters are handled correctly"""
        special_response = "Reply with special chars: <>&\"'✓"
        mock_service.return_value.generate_response.return_value = special_response

        response = self.client.post(
            "/",
            data={
                "prompt": "Test",
                "tone": "professional",
                "length": "medium"
            }
        )

        html = response.get_data(as_text=True)
        # Special characters should be escaped/handled properly in HTML
        self.assertIn("Reply with special chars", html)

    @patch("app.routes.LLMService")
    def test_generated_reply_is_html_escaped(self, mock_service):
        """Generated content must render as text, not executable markup."""
        mock_service.return_value.generate_response.return_value = (
            "Reply <script>alert('xss')</script> & safe"
        )

        response = self.client.post(
            "/",
            data={"prompt": "Test", "tone": "professional", "length": "medium"},
        )
        html = response.get_data(as_text=True)

        self.assertIn(
            "Reply &lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt; &amp; safe", html
        )
        self.assertNotIn("<script>alert('xss')</script>", html)

    @patch("app.routes.LLMService")
    def test_sensitive_input_remains_visible_in_redisplayed_form(self, mock_service):
        mock_service.return_value.generate_response.return_value = "Safe reply"

        response = self.client.post(
            "/",
            data={
                "prompt": "Passport number E1234567 and NRIC S1234567D",
                "tone": "professional",
                "length": "short",
                "additional_context": "Phone +65 9123 4567, card 4111 1111 1111 1111",
            },
        )
        html = response.get_data(as_text=True)

        for private_value in (
            "E1234567", "S1234567D", "+65 9123 4567", "4111 1111 1111 1111",
        ):
            self.assertIn(private_value, html)


if __name__ == "__main__":
    unittest.main()
