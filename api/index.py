import sys
import os
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly in Vercel Serverless environment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app
