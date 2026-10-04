import os
import unittest
from unittest.mock import patch
from backend.analyzer import analyze_codebase
from backend.engine import ArchitectureEngine
from backend.miro_client import MiroClient

class TestActionE2E(unittest.TestCase):
    @patch("requests.post")
    @patch("requests.get")
    def test_full_action_pipeline_simulation(self, mock_get, mock_post):
        # 1. Mock Miro API responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"id": "test_board_id", "name": "E2E Test Board"}
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "shape_1", "type": "shape"}

        # 2. Ingest local directory
        codebase_data = analyze_codebase(source_type="local", source_value=os.path.join(os.getcwd(), "backend"))
        self.assertIn("file_tree", codebase_data)

        # 3. Synthesize architecture using universal ArchitectureEngine
        engine = ArchitectureEngine()
        arch_data = engine._get_fallback()
        self.assertIn("nodes", arch_data)

        # 4. Synchronize multi-tier visual layout into Miro board
        client = MiroClient(access_token="mock_token", board_id="test_board_id")
        sync_res = client.sync_architecture_diagram(arch_data=arch_data, perspective="overview")

        self.assertIn("board_url", sync_res)
        self.assertEqual(sync_res["board_id"], "test_board_id")

if __name__ == "__main__":
    unittest.main()
