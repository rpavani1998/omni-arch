import unittest
from unittest.mock import patch, MagicMock
from backend.miro_client import MiroClient, TYPE_STYLES

class TestMiroClient(unittest.TestCase):
    def setUp(self):
        self.client = MiroClient(access_token="mock_token_123", board_id="mock_board_456")

    def test_type_styles_available(self):
        self.assertIn("frontend", TYPE_STYLES)
        self.assertIn("service", TYPE_STYLES)
        self.assertIn("database", TYPE_STYLES)
        self.assertIn("cache", TYPE_STYLES)

    def test_sync_architecture_diagram_initial_creation(self):
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
            mock_get.return_value.json.return_value = {"data": []}
            
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": "item_123", "type": "shape"}

            result = self.client.sync_architecture_diagram(arch_data, perspective="overview")
            
            self.assertIn("board_url", result)
            self.assertEqual(result["created_nodes"], 3)
            self.assertEqual(result["board_id"], "mock_board_456")
            self.assertEqual(result["sync_mode"], "initial_creation")

    def test_sync_architecture_diagram_incremental_pr_update(self):
        """Simulate a PR that updates an existing service in-place and adds 1 new service."""
        arch_data = {
            "system_title": "Test Architecture",
            "perspective": "overview",
            "nodes": [
                {"id": "c1", "name": "Frontend Web App", "type": "frontend", "layer_id": "layer_presentation", "description": "Updated React 19 SPA"},
                {"id": "c2", "name": "Order Service", "type": "service", "layer_id": "layer_services", "description": "New Microservice added in PR"}
            ],
            "connections": [
                {"from": "c1", "to": "c2", "label": "HTTPS REST"}
            ],
            "summary": "Updated system architecture."
        }

        # Mock existing board having 'Frontend Web App' shape already in that frame
        existing_items = [
            {
                "id": "shape_frontend_999",
                "type": "shape",
                "data": {"content": "<p><strong>Frontend Web App</strong></p>"},
                "position": {"x": 0, "y": 0}
            }
        ]

        with patch("requests.get") as mock_get, patch("requests.post") as mock_post, patch("requests.patch") as mock_patch:
            # Mock get items
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"data": existing_items}

            # Mock create shape for the new service
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": "shape_order_888", "type": "shape"}

            # Mock in-place patch for existing service
            mock_patch.return_value.status_code = 200
            mock_patch.return_value.json.return_value = {"id": "shape_frontend_999", "type": "shape"}

            result = self.client.sync_architecture_diagram(arch_data, perspective="overview")

            self.assertEqual(result["updated_nodes"], 1, "Existing 'Frontend Web App' should be updated in-place via PATCH")
            self.assertEqual(result["created_nodes"], 1, "New 'Order Service' should be created via POST")
            self.assertEqual(result["sync_mode"], "incremental_update")
            # Verify PATCH was called on the existing shape ID
            mock_patch.assert_called()

if __name__ == "__main__":
    unittest.main()
