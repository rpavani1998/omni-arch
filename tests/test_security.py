import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rate_limiter_allows_under_limit(self):
        for i in range(5):
            resp = self.client.get("/health")
            self.assertEqual(resp.status_code, 200)

    def test_correlation_id_and_tracing(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("X-Correlation-ID", resp.headers)
        self.assertTrue(len(resp.headers["X-Correlation-ID"]) > 8)

        # Custom correlation ID is preserved
        custom_cid = "test-cid-998877"
        resp2 = self.client.get("/health", headers={"X-Correlation-ID": custom_cid})
        self.assertEqual(resp2.headers.get("X-Correlation-ID"), custom_cid)

    def test_healthz_endpoint_subsystem_inspection(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("subsystems", data)
        self.assertEqual(data["subsystems"].get("analyzer"), "ready")

    def test_telemetry_path_scrubbing(self):
        from backend.security import sanitize_telemetry_path
        raw_path = "/api/oauth/callback"
        dirty_query = "code=secret_code_123&state=state_xyz&access_token=sk-998877"
        clean = sanitize_telemetry_path(raw_path, dirty_query)
        self.assertNotIn("secret_code_123", clean)
        self.assertNotIn("sk-998877", clean)
        self.assertIn("[REDACTED]", clean)


if __name__ == "__main__":
    unittest.main()