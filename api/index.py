import sys
import os

api_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(api_dir)

for d in [api_dir, root_dir]:
    if d and d not in sys.path:
        sys.path.insert(0, d)

try:
    from backend.main import app
except ImportError:
    from main import app

