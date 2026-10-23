import io
import json
import unittest
from unittest.mock import Mock, patch

from app import create_app


class InboxSlothTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "OLLAMA_TIMEOUT": 1,
                "MAX_TEXT_CHARS": 100,
            }
        )
        self.client = self.app.test_client()

    def upload(self, content=b"[10:00] Priya: Demo Friday.", filename="chat.txt"):
        return self.client.post(
            "/api/summarize",
            data={"file": (io.BytesIO(content), filename)},
            content_type="multipart/form-data",
        )

    def test_homepage_and_sample_are_available(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/sample_chat.txt").status_code, 200)

    @patch("ai_service.requests.get")
    def test_health_reports_model_status(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": [{"name": "gemma3:1b"}]},
        )
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["model_installed"])

    def test_upload_validation_errors(self):
        self.assertEqual(self.upload(b"", "chat.txt").status_code, 400)
        self.assertEqual(self.upload(b"hello", "chat.pdf").status_code, 400)
        self.assertEqual(self.upload(b"\xff", "chat.txt").json["code"], "invalid_encoding")
        self.assertEqual(self.upload(b"x" * 101, "chat.txt").json["code"], "text_too_long")

    @patch("ai_service.requests.post")
    def test_valid_upload_returns_structured_digest(self, mock_post):
        digest = {
            "summary": "The group is preparing for a demo.",
            "key_points": ["The demo is on Friday."],
            "announcements": [],
            "tasks": [],
            "deadlines": [{"event": "Demo", "date": "Friday"}],
            "pending_decisions": [],
        }
        mock_post.return_value = Mock(
            raise_for_status=lambda: None,
            json=lambda: {"response": json.dumps(digest)},
        )
        response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["digest"], digest)

    @patch("ai_service.requests.post", side_effect=__import__("requests").Timeout)
    def test_timeout_is_actionable(self, _mock_post):
        response = self.upload()
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json["code"], "ollama_timeout")

    @patch("ai_service.requests.post")
    def test_malformed_and_missing_model_output_are_rejected(self, mock_post):
        mock_post.return_value = Mock(
            raise_for_status=lambda: None,
            json=lambda: {"response": "not json"},
        )
        response = self.upload()
        self.assertEqual(response.json["code"], "invalid_model_json")

        mock_post.return_value = Mock(
            raise_for_status=lambda: None,
            json=lambda: {"response": json.dumps({"summary": "Only a summary"})},
        )
        response = self.upload()
        self.assertEqual(response.json["code"], "missing_model_fields")

    @patch("ai_service.requests.post", side_effect=__import__("requests").ConnectionError)
    def test_ollama_unavailable_is_actionable(self, _mock_post):
        response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["code"], "ollama_unavailable")


if __name__ == "__main__":
    unittest.main()
