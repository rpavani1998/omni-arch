import unittest
import time
from backend.security import SlidingWindowRateLimiter

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=2)

    def test_rate_limiter_allows_under_limit(self):
        for i in range(5):
            allowed, limit, remaining, reset_sec = self.limiter.check_rate_limit("1.2.3.4", "/api/sample")
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
            self.assertEqual(remaining, 4 - i)

    def test_rate_limiter_blocks_over_limit(self):
        # 5 requests should pass
        for _ in range(5):
            self.limiter.check_rate_limit("1.2.3.4", "/api/sample")
        
        # 6th request should be blocked
        allowed, limit, remaining, reset_sec = self.limiter.check_rate_limit("1.2.3.4", "/api/sample")
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(reset_sec, 0)

    def test_rate_limiter_resets_after_window(self):
        limiter = SlidingWindowRateLimiter(default_limit=2, window_seconds=1)
        limiter.check_rate_limit("user1", "/api/test")
        limiter.check_rate_limit("user1", "/api/test")
        
        allowed, _, _, _ = limiter.check_rate_limit("user1", "/api/test")
        self.assertFalse(allowed)

        time.sleep(1.1)
        allowed, _, remaining, _ = limiter.check_rate_limit("user1", "/api/test")
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)

if __name__ == "__main__":
    unittest.main()
