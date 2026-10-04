import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from analyzer import CodebaseAnalyzer
from qwen_engine import QwenEngine
from miro_client import MiroClient

load_dotenv()

app = FastAPI(title="QwenArch API", description="Codebase to Miro Architecture Engine powered by Qwen")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qwen_engine = QwenEngine()
miro_client = MiroClient()

class AnalyzeRequest(BaseModel):
    source_type: str  # "github", "local", "prompt"
    source_value: str
    provider: Optional[str] = "auto" # "ollama", "modelscope", "auto"
    perspective: Optional[str] = "overview" # predefined perspective id
    custom_instructions: Optional[str] = "" # user focus / customization instructions

class SyncMiroRequest(BaseModel):
    architecture: Dict[str, Any]
    offset_x: Optional[float] = -300
    offset_y: Optional[float] = -150

SAMPLE_REPOS = [
    {
        "name": "E-Commerce Microservices",
        "description": "Multi-tier microservices with Next.js, FastAPI, Kafka, Redis, and PostgreSQL.",
        "type": "prompt",
        "source": """
        Project: CloudShop Microservices
        Services:
        - Web-Storefront: Next.js 15, Tailwind CSS, SSR React components for catalog, cart, and checkout.
        - API-Gateway: Envoy Proxy / Kong routing /api/v1 requests with JWT authentication and rate limiting.
        - Order-Service: Go (Golang) microservice handling order state machine, Stripe checkout webhooks.
        - Product-Catalog-Service: Python FastAPI service managing product taxonomy, categories, elasticsearch search.
        - Inventory-Service: Node.js / TypeScript tracking warehouse inventory and stock reservation.
        - Notification-Service: Python worker listening to Kafka events to dispatch emails via SendGrid and SMS via Twilio.
        Storage & Queues:
        - Postgres-Orders: Primary relational database for transactions and orders.
        - Redis-Cache: In-memory store for session tokens, shopping cart states, and hot product caching.
        - Kafka-Event-Bus: Distributed event stream for OrderCreated, PaymentCompleted, StockUpdated events.
        """
    },
    {
        "name": "AI Agent Multimodal Platform",
        "description": "Distributed LLM agentic architecture with Python, LangGraph, Vector DB, and WebSockets.",
        "type": "prompt",
        "source": """
        Project: VisionAgent AI Studio
        Architecture:
        - Web-App: React + TypeScript canvas interface with real-time collaborative streaming via WebSockets.
        - Ingress-Router: Traefik edge router with SSL termination and API key validation.
        - Agent-Orchestrator: Python FastAPI + LangGraph service running multi-agent reasoning loops.
        - Model-Inference-Engine: vLLM & Qwen-VL server for visual reasoning and multimodal image understanding.
        - Knowledge-Retrieval-Service: FastEmbed + Qdrant Vector Database for semantic search and document RAG.
        - Task-Queue: Celery + Redis for asynchronous long-running background evaluations.
        - Storage: AWS S3 bucket for media attachments, PostgreSQL for user accounts and chat history.
        """
    },
    {
        "name": "Fintech Real-Time Payment Gateway",
        "description": "High-throughput financial ledger with Go, gRPC, CockroachDB, and RabbitMQ.",
        "type": "prompt",
        "source": """
        Project: PayPulse Financial Infrastructure
        Architecture:
        - Mobile & Merchant SDKs: Flutter and React Native client libraries.
        - API-Gateway: gRPC-Web gateway with mutual TLS (mTLS) and fraud-detection pre-flight checks.
        - Auth-Service: Rust identity service issuing cryptographic tokens and hardware security module (HSM) validation.
        - Ledger-Engine: Go service executing double-entry bookkeeping with strict ACID guarantees.
        - Settlement-Worker: Kotlin service executing batch settlements with banking ACH networks.
        - Database: CockroachDB multi-region distributed SQL database.
        - Audit-Stream: Apache Kafka audit log with immutable event storage.
        """
    }
]

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
@router.get("/api")
def health():
    return {"status": "ok", "app": "QwenArch"}

@router.get("/board-info")
def get_board_info():
    try:
        info = miro_client.get_board_info()
        return {
            "success": True,
            "board_id": info.get("id"),
            "name": info.get("name"),
            "view_link": info.get("viewLink"),
            "owner": info.get("owner", {}).get("name"),
            "team": info.get("team", {}).get("name")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/sample-repos")
def get_sample_repos():
    return SAMPLE_REPOS

@router.post("/analyze")
def analyze_codebase(req: AnalyzeRequest):
    try:
        if req.source_type == "github":
            codebase_data = CodebaseAnalyzer.clone_and_scan_github(req.source_value)
        elif req.source_type == "local":
            codebase_data = CodebaseAnalyzer.scan_directory(req.source_value)
        elif req.source_type == "prompt":
            codebase_data = {
                "root_name": "Custom System",
                "languages": {"Architecture Spec": 1},
                "file_tree": ["system_spec.txt"],
                "key_files": {"system_spec.txt": req.source_value}
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        analysis_result = qwen_engine.analyze_architecture(
            codebase_data, 
            provider=req.provider or "modelscope",
            perspective=req.perspective or "overview",
            custom_instructions=req.custom_instructions or ""
        )
        return {
            "success": True,
            "architecture": analysis_result["architecture"],
            "usage": analysis_result["usage"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-stream")
def analyze_codebase_stream(req: AnalyzeRequest):
    try:
        if req.source_type == "github":
            codebase_data = CodebaseAnalyzer.clone_and_scan_github(req.source_value)
        elif req.source_type == "local":
            codebase_data = CodebaseAnalyzer.scan_directory(req.source_value)
        elif req.source_type == "prompt":
            codebase_data = {
                "root_name": "Custom System",
                "languages": {"Architecture Spec": 1},
                "file_tree": ["system_spec.txt"],
                "key_files": {"system_spec.txt": req.source_value}
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        return StreamingResponse(
            qwen_engine.stream_architecture_analysis(
                codebase_data, 
                provider=req.provider or "modelscope",
                perspective=req.perspective or "overview",
                custom_instructions=req.custom_instructions or ""
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-miro")
def sync_to_miro(req: SyncMiroRequest):
    try:
        res = miro_client.sync_architecture_diagram(
            arch_data=req.architecture,
            start_x=req.offset_x or -300,
            start_y=req.offset_y or -150
        )
        return {
            "success": True,
            "result": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Paths to dist and static folders
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
FRONTEND_PUBLIC = ROOT_DIR / "frontend" / "public"
SLIDES_HTML = FRONTEND_DIST / "slides.html" if (FRONTEND_DIST / "slides.html").exists() else ROOT_DIR / "slides.html"

# Include router for root, /api, and /api/index.py to handle all Vercel proxying patterns
app.include_router(router, prefix="")
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/api/index.py")

# Serve static assets if dist exists
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

if (FRONTEND_DIST / "slides").exists():
    app.mount("/slides", StaticFiles(directory=str(FRONTEND_DIST / "slides")), name="slides")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_path = FRONTEND_DIST / "favicon.ico"
    if fav_path.exists():
        return FileResponse(str(fav_path))
    fav_pub = FRONTEND_PUBLIC / "favicon.ico"
    if fav_pub.exists():
        return FileResponse(str(fav_pub))
    return HTMLResponse(content="", status_code=204)

@app.get("/slides.html", include_in_schema=False)
def get_slides():
    if SLIDES_HTML.exists():
        return FileResponse(str(SLIDES_HTML))
    return HTMLResponse("<h1>Slides not found</h1>", status_code=404)

@app.get("/", include_in_schema=False)
def serve_spa():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "app": "QwenArch"}

@app.get("/{full_path:path}", include_in_schema=False)
def spa_catch_all(full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/") or full_path == "api" or full_path.startswith("api/index.py"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    # Check if a static file in dist matches
    potential_file = FRONTEND_DIST / full_path
    if potential_file.exists() and potential_file.is_file():
        return FileResponse(str(potential_file))
        
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "app": "QwenArch"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


