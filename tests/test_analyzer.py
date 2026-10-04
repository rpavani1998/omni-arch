import os
import unittest
from backend.analyzer import analyze_codebase, CodebaseAnalyzer

class TestCodebaseAnalyzer(unittest.TestCase):
    def test_local_directory_scan(self):
        backend_dir = os.path.join(os.getcwd(), "backend")
        res = CodebaseAnalyzer.scan_directory(backend_dir)
        
        self.assertIn("file_tree", res)
        self.assertIn("key_files", res)
        self.assertIn("languages", res)
        self.assertTrue(res["total_files_scanned"] > 0)
        
        # Verify excluded paths are filtered out
        for f in res["file_tree"]:
            self.assertFalse(f.endswith(".pyc"))
            self.assertFalse("__pycache__" in f)

    def test_analyze_codebase_local_source(self):
        backend_dir = os.path.join(os.getcwd(), "backend")
        res = analyze_codebase(source_type="local", source_value=backend_dir)
        
        self.assertIn("file_tree", res)
        self.assertEqual(res["source_type"], "local")

if __name__ == "__main__":
    unittest.main()
