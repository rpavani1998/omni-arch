import unittest
from backend.qwen_engine import QwenEngine

class TestQwenEngine(unittest.TestCase):
    def setUp(self):
        self.engine = QwenEngine()

    def test_fallback_schema(self):
        arch = self.engine._get_fallback()
        
        self.assertIn("system_title", arch)
        self.assertIn("nodes", arch)
        self.assertIn("connections", arch)
        self.assertIn("summary", arch)
        self.assertTrue(len(arch["nodes"]) > 0)
        
        for node in arch["nodes"]:
            self.assertIn("id", node)
            self.assertIn("name", node)
            self.assertIn("type", node)
            self.assertIn("layer_id", node)

    def test_clean_json_markdown_fences(self):
        raw_output = """```json
{
  "system_title": "Test App",
  "nodes": [
    {"id": "n1", "name": "Frontend", "layer_id": "layer_presentation", "type": "frontend"}
  ],
  "connections": []
}
```"""
        parsed = self.engine._parse_json_response(raw_output)
        self.assertEqual(parsed["system_title"], "Test App")
        self.assertEqual(len(parsed["nodes"]), 1)

    def test_clean_json_repair_trailing_comma(self):
        raw_output = '{"system_title": "Repaired App", "nodes": [{"id": "n1", "name": "API", "layer_id": "layer_gateway", "type": "gateway",}], "connections": []}'
        parsed = self.engine._parse_json_response(raw_output)
        self.assertEqual(parsed["system_title"], "Repaired App")

if __name__ == "__main__":
    unittest.main()
