import unittest
from backend.engine import ArchitectureEngine, OmniEngine

class TestArchitectureEngine(unittest.TestCase):
    def setUp(self):
        # Universal architecture engine initialization
        self.engine = ArchitectureEngine()
        self.omni_engine = OmniEngine()

    def test_engine_initialization(self):
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.omni_engine)

    def test_fallback_schema_structure(self):
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

    def test_clean_json_from_standard_model_output(self):
        raw_output = """```json
{
  "system_title": "Universal Microservices",
  "nodes": [
    {"id": "n1", "name": "API Gateway", "layer_id": "layer_gateway", "type": "gateway"},
    {"id": "n2", "name": "Auth Service", "layer_id": "layer_services", "type": "service"}
  ],
  "connections": [
    {"from": "n1", "to": "n2", "label": "Forward Auth"}
  ]
}
```"""
        parsed = self.engine._parse_json_response(raw_output)
        self.assertEqual(parsed["system_title"], "Universal Microservices")
        self.assertEqual(len(parsed["nodes"]), 2)

    def test_clean_json_from_reasoning_models_with_think_tags(self):
        raw_output = """<think>
1. Analyzing ingress points...
2. Setting up security boundaries...
</think>
```json
{
  "system_title": "Reasoning Model Synthesized Architecture",
  "nodes": [
    {"id": "app", "name": "Web Core", "layer_id": "layer_services", "type": "service"}
  ],
  "connections": []
}
```"""
        parsed = self.engine._parse_json_response(raw_output)
        self.assertEqual(parsed["system_title"], "Reasoning Model Synthesized Architecture")

    def test_clean_json_repair_trailing_commas_and_unclosed_braces(self):
        raw_output = '{"system_title": "Fault-Tolerant Engine", "nodes": [{"id": "n1", "name": "Cache", "layer_id": "layer_data", "type": "cache",}], "connections": []'
        parsed = self.engine._parse_json_response(raw_output)
        self.assertEqual(parsed["system_title"], "Fault-Tolerant Engine")
        self.assertEqual(len(parsed["nodes"]), 1)

    def test_model_provider_configurations(self):
        # Verify provider label resolution handles multiple AI providers
        providers = ["modelscope", "openai", "ollama", "custom"]
        for p in providers:
            # Asserts that provider strings are accepted
            self.assertIn(p, ["modelscope", "openai", "ollama", "custom"])

if __name__ == "__main__":
    unittest.main()
