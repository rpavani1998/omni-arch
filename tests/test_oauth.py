import unittest
import tempfile
import os
from backend.oauth import MiroOAuthManager, MultiTenantInstallationStore

class TestOAuth(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_path = os.path.join(self.temp_dir.name, "test_installations.json")
        self.store = MultiTenantInstallationStore(storage_file=self.store_path)
        self.oauth = MiroOAuthManager()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_state_generation_and_validation(self):
        auth_data = self.oauth.generate_authorization_url()
        state = auth_data["state"]
        self.assertTrue(bool(state))
        self.assertTrue(self.oauth.validate_state(state))
        # Re-validation of consumed state should fail
        self.assertFalse(self.oauth.validate_state(state))

    def test_installation_store_crud(self):
        team_id = "test_team_99"
        data = {
            "access_token": "token_12345",
            "refresh_token": "refresh_67890",
            "user_id": "user_42",
            "expires_in": 3600
        }
        self.store.save_installation(team_id, data)
        
        inst = self.store.get_installation(team_id)
        self.assertIsNotNone(inst)
        self.assertEqual(inst["access_token"], "token_12345")
        self.assertEqual(inst["user_id"], "user_42")

        # Test listing
        listed = self.store.list_installations()
        self.assertIn(team_id, listed)
        # Verify access token and refresh token are not leaked in list summary
        self.assertNotIn("access_token", listed[team_id])

        # Test delete
        self.assertTrue(self.store.delete_installation(team_id))
        self.assertIsNone(self.store.get_installation(team_id))

    def test_kv_storage_adapter(self):
        # Test KV REST backend simulation
        os.environ["KV_REST_API_URL"] = "https://mock-kv.upstash.io"
        os.environ["KV_REST_API_TOKEN"] = "mock_token"
        kv_store = MultiTenantInstallationStore()
        self.assertTrue(kv_store.is_kv_enabled())
        # Clean up env
        del os.environ["KV_REST_API_URL"]
        del os.environ["KV_REST_API_TOKEN"]

if __name__ == "__main__":
    unittest.main()

