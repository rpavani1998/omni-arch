import sys
import os
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

for p in [backend_dir, root_dir, current_dir]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

try:
    try:
        from backend.main import app
    except ImportError:
        from main import app
except Exception as e:
    err_trace = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="QwenArch Diagnostic Mode")
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    def diagnostic_fallback(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend serverless function initialization failed",
                "details": str(e),
                "trace": err_trace,
                "sys_path": sys.path,
                "current_dir": current_dir,
                "root_dir": root_dir,
                "backend_dir": backend_dir,
                "root_files": os.listdir(root_dir) if os.path.exists(root_dir) else [],
                "backend_files": os.listdir(backend_dir) if os.path.exists(backend_dir) else []
            }
        )
