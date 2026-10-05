import os
import unittest
from backend.analyzer import analyze_codebase, CodebaseAnalyzer, redact_secrets, extract_architectural_signatures

class TestCodebaseAnalyzer(unittest.TestCase):
    def test_local_directory_scan(self):
        backend_dir = os.path.join(os.getcwd(), "backend")
        res = CodebaseAnalyzer.scan_directory(backend_dir)
        
        self.assertIn("file_tree", res)
        self.assertIn("key_files", res)
        self.assertIn("languages", res)
        self.assertIn("signatures", res)
        self.assertTrue(res["total_files_scanned"] > 0)
        
        # Verify signatures dictionary structure
        self.assertIn("discovered_routes", res["signatures"])
        self.assertIn("discovered_models", res["signatures"])
        self.assertIn("discovered_integrations", res["signatures"])

        # Verify excluded paths are filtered out
        for f in res["file_tree"]:
            self.assertFalse(f.endswith(".pyc"))
            self.assertFalse("__pycache__" in f)

    def test_secret_redaction(self):
        dirty_snippet = """
        AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
        GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        OPENAI_API_KEY = "sk-1234567890abcdef1234567890abcdef"
        DB_URL = "postgres://admin:supersecretpassword@db.example.com:5432/production"
        """
        clean = redact_secrets(dirty_snippet)
        
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", clean)
        self.assertNotIn("ghp_1234567890abcdef", clean)
        self.assertNotIn("sk-1234567890abcdef", clean)
        self.assertNotIn("supersecretpassword", clean)
        self.assertIn("[REDACTED_AWS_KEY]", clean)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", clean)

    def test_architectural_signatures_extraction(self):
        code_snippet = """
        from fastapi import FastAPI, APIRouter
        from pydantic import BaseModel
        import redis

        app = FastAPI()
        router = APIRouter()

        class UserAccount(BaseModel):
            id: str
            email: str

        redis_client = redis.Redis(host='localhost', port=6379)

        @app.get("/api/v1/health")
        def health():
            return {"status": "ok"}

        @router.post("/api/v1/users")
        def create_user(user: UserAccount):
            return user
        """
        sigs = extract_architectural_signatures(code_snippet, ".py")
        
        self.assertTrue(any("GET /api/v1/health" in r for r in sigs["routes"]))
        self.assertTrue(any("POST /api/v1/users" in r for r in sigs["routes"]))
    def test_path_traversal_rejection(self):
        # Attempting to scan restricted system paths should raise PermissionError or FileNotFoundError
        with self.assertRaises((PermissionError, FileNotFoundError)):
            CodebaseAnalyzer.scan_directory("/etc")

        with self.assertRaises((PermissionError, FileNotFoundError)):
            CodebaseAnalyzer.scan_directory("../../../etc/passwd")

    def test_expanded_secret_patterns(self):
        slack_mock = "xoxb-" + "1234567890-" + "abcdef123456"
        google_mock = "AIzaSy" + "D-1234567890abcdef1234567890abcde"
        stripe_mock = "sk_" + "live_" + "51Abcdefghijklmnopqrstuvw"
        jwt_mock = "eyJhbGci" + "OiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSignature1234567"
        pat_mock = "github_" + "pat_" + "11AAAAAAA0123456789abcdefghijklmnopqrstuvwxyz0123456789abcdefghijkl"

        dirty = f"""
        SLACK_TOKEN = "{slack_mock}"
        GOOGLE_KEY = "{google_mock}"
        STRIPE_KEY = "{stripe_mock}"
        JWT = "{jwt_mock}"
        GITHUB_PAT = "{pat_mock}"
        """
        clean = redact_secrets(dirty)
        self.assertNotIn(slack_mock, clean)
        self.assertNotIn(google_mock, clean)
        self.assertNotIn(stripe_mock, clean)
        self.assertNotIn(jwt_mock, clean)
        self.assertNotIn(pat_mock, clean)
        self.assertIn("[REDACTED_SLACK_TOKEN]", clean)
        self.assertIn("[REDACTED_GOOGLE_API_KEY]", clean)
        self.assertIn("[REDACTED_STRIPE_KEY]", clean)
        self.assertIn("[REDACTED_JWT_TOKEN]", clean)
        self.assertIn("[REDACTED_GITHUB_PAT]", clean)

if __name__ == "__main__":
    unittest.main()
