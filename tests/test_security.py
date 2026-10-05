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

    def test_security_headers_present(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content-Security-Policy", resp.headers)
        self.assertIn("frame-ancestors", resp.headers["Content-Security-Policy"])
        self.assertIn("X-Content-Type-Options", resp.headers)
        self.assertIn("X-XSS-Protection", resp.headers)
        self.assertIn("Referrer-Policy", resp.headers)


if __name__ == "__main__":
    unittest.main()