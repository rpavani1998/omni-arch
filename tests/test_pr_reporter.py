import unittest
from unittest.mock import patch, MagicMock
from backend.pr_reporter import PRArchitectureReporter

class TestPRReporter(unittest.TestCase):
    def test_detect_change_severity_major(self):
        sync_result = {
            "sync_mode": "incremental_update",
            "created_nodes": 2,
            "updated_nodes": 1,
            "deleted_nodes": 0,
            "board_url": "https://miro.com/app/board/123",
            "frame_title": "System Architecture"
        }
        arch_data = {"system_title": "CloudShop"}
        meta = PRArchitectureReporter.detect_change_severity(sync_result, arch_data)
        self.assertEqual(meta["severity"], "MAJOR")
        self.assertIn("CRITICAL", meta["badge"])

    def test_detect_change_severity_moderate(self):
        sync_result = {
            "sync_mode": "incremental_update",
            "created_nodes": 0,
            "updated_nodes": 3,
            "deleted_nodes": 0,
            "board_url": "https://miro.com/app/board/123",
            "frame_title": "System Architecture"
        }
        arch_data = {"system_title": "CloudShop"}
        meta = PRArchitectureReporter.detect_change_severity(sync_result, arch_data)
        self.assertEqual(meta["severity"], "MODERATE")

    def test_generate_pr_markdown_comment(self):
        sync_result = {
            "sync_mode": "incremental_update",
            "created_nodes": 1,
            "updated_nodes": 2,
            "deleted_nodes": 0,
            "board_url": "https://miro.com/app/board/123/?moveToWidget=456",
            "frame_title": "System Architecture — System Architecture (HLD)",
            "total_items": 12
        }
        arch_data = {
            "system_title": "OmniArch",
            "nodes": [
                {"id": "s1", "name": "API Gateway", "type": "gateway", "tech": "FastAPI"},
                {"id": "s2", "name": "User Service", "type": "service", "tech": "Go"}
            ],
            "insights": {
                "strengths": ["Clean separation of concerns"],
                "recommendations": ["Verify zero-trust authentication on new gateway routes"]
            }
        }
        comment = PRArchitectureReporter.generate_pr_markdown_comment(sync_result, arch_data, "overview", "test/repo")
        self.assertIn("OmniArch Architecture Sync", comment)
        self.assertIn("API Gateway", comment)
        self.assertIn("https://miro.com/app/board/123/?moveToWidget=456", comment)
        self.assertIn("<!-- omniarch-pr-architecture-comment -->", comment)

    @patch("requests.get")
    @patch("requests.post")
    def test_post_pr_comment_new(self, mock_post, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [] # No existing comment
        
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": 999}

        sync_result = {"board_url": "https://miro.com/app/board/123"}
        arch_data = {"nodes": []}
        
        # Test with event path
        with patch.dict("os.environ", {"GITHUB_TOKEN": "mock_gh_token", "GITHUB_REPOSITORY": "test/repo", "GITHUB_EVENT_PATH": "/tmp/event.json"}):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", unittest.mock.mock_open(read_data='{"pull_request": {"number": 42}}')):
                    res = PRArchitectureReporter.post_or_update_pr_comment(sync_result, arch_data, "overview")
                    self.assertTrue(res)
                    mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
