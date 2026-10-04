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
                self.assertEqual(res.get("name"), "Refreshed Board")


if __name__ == "__main__":
    unittest.main()
