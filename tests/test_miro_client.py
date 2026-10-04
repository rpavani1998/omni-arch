import unittest
from unittest.mock import patch
from backend.miro_client import MiroClient, TYPE_STYLES

class TestMiroClient(unittest.TestCase):
    def setUp(self):
        self.client = MiroClient(access_token="mock_token_123", board_id="mock_board_456")

    def test_type_styles_available(self):
        self.assertIn("frontend", TYPE_STYLES)
        self.assertIn("service", TYPE_STYLES)
        self.assertIn("database", TYPE_STYLES)
        self.assertIn("cache", TYPE_STYLES)

    def test_sync_architecture_diagram_mocked(self):
        arch_data = {
            "system_title": "Test Architecture",
            "perspective": "overview",
            "nodes": [
                {"id": "c1", "name": "Frontend Web App", "type": "frontend", "layer_id": "layer_presentation", "description": "React SPA"},
                {"id": "c2", "name": "REST API Gateway", "type": "gateway", "layer_id": "layer_gateway", "description": "FastAPI"},
                {"id": "c3", "name": "Postgres DB", "type": "database", "layer_id": "layer_data", "description": "Primary Relational DB"}
            ],
            "connections": [
                {"from": "c1", "to": "c2", "label": "HTTPS REST"},
                {"from": "c2", "to": "c3", "label": "SQL Queries"}
            ],
            "summary": "Three-tier web application architecture with React, FastAPI, and Postgres."
        }

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"id": "mock_board_456", "name": "Test Board"}
            
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": "item_123", "type": "shape"}

            result = self.client.sync_architecture_diagram(arch_data, perspective="overview")
            
            self.assertIn("board_url", result)
            self.assertIn("created_nodes", result)
            self.assertIn("created_connectors", result)
            self.assertEqual(result["board_id"], "mock_board_456")

if __name__ == "__main__":
    unittest.main()
