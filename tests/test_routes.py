import unittest
from unittest.mock import patch

from app import create_app


class IndexRouteTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
