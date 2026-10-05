import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.oauth import installation_store, oauth_manager
from backend.miro_client import MiroClient

class TestMarketplaceFeatures(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_security_headers_present(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content-Security-Policy", resp.headers)
        self.assertIn("frame-ancestors", resp.headers["Content-Security-Policy"])
        self.assertIn("X-Content-Type-Options", resp.headers)

    def test_oauth_uninstall_webhook(self):
        # Setup an installation
        team_id = "test_uninstall_team_101"
        installation_store.save_installation(team_id, {
            "access_token": "token_to_revoke",
            "refresh_token": "refresh_to_revoke"
        })
        self.assertIsNotNone(installation_store.get_installation(team_id))

        # Invoke uninstall webhook
        resp = self.client.post("/api/oauth/uninstall", json={"team_id": team_id, "event": "app.uninstalled"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("success"))

        # Verify installation was revoked and removed from storage
        self.assertIsNone(installation_store.get_installation(team_id))

    def test_miro_client_auto_token_refresh_on_401(self):
        client = MiroClient(access_token="old_expired_token", board_id="board_123", team_id="team_auto_refresh")
        
        # Mock responses: first call returns 401, second call returns 200
        mock_401 = MagicMock()
        mock_401.status_code = 401
        
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"id": "board_123", "name": "Refreshed Board"}
        mock_200.raise_for_status = MagicMock()

        with patch("requests.get", side_effect=[mock_401, mock_200]):
            with patch.object(oauth_manager, "refresh_access_token", return_value="new_fresh_token_456") as mock_refresh:
                res = client.get_board_info()
                mock_refresh.assert_called_once_with("team_auto_refresh")
                self.assertEqual(client.access_token, "new_fresh_token_456")
    def test_analyze_endpoint_execution(self):
        with patch("backend.main.engine.analyze_architecture") as mock_engine:
            mock_engine.return_value = {
                "architecture": {"nodes": [{"id": "svc1", "name": "API Service", "type": "service"}], "edges": []},
                "usage": {"total_tokens": 150, "duration_ms": 200, "model": "test-model", "provider": "TestProvider"}
            }
            resp = self.client.post("/api/analyze", json={
                "source_type": "prompt",
                "source_value": "FastAPI service with PostgreSQL database",
                "perspective": "overview"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertEqual(len(data["architecture"]["nodes"]), 1)

    def test_scaffold_endpoint_execution(self):
        with patch("backend.main.engine.scaffold_component_boilerplate") as mock_scaffold:
            mock_scaffold.return_value = {
                "code": "from fastapi import FastAPI\napp = FastAPI()",
                "dockerfile": "FROM python:3.10",
                "docker_compose": "version: '3.8'",
                "quickstart": "# Setup"
            }
            resp = self.client.post("/api/scaffold", json={
                "component_name": "AuthService",
                "component_type": "service",
                "tech": "FastAPI"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertIn("from fastapi", data["scaffold"]["code"])


if __name__ == "__main__":
    unittest.main()
