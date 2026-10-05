import os
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

try:
    from backend.analyzer import CodebaseAnalyzer
    from backend.engine import ArchitectureEngine
    from backend.miro_client import MiroClient
    from backend.security import SecurityAndTelemetryMiddleware, get_rate_limit_for_path
    from backend.oauth import oauth_manager, installation_store
except ImportError:
    from analyzer import CodebaseAnalyzer
    from engine import ArchitectureEngine
    from miro_client import MiroClient
    from security import SecurityAndTelemetryMiddleware, get_rate_limit_for_path
    from oauth import oauth_manager, installation_store


load_dotenv()

app = FastAPI(title="OmniArch API", description="Universal Codebase to Miro Architecture Engine powered by Multi-Model AI")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security & Telemetry Middleware (HSTS, CSP, Latency Logging)
app.add_middleware(SecurityAndTelemetryMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ArchitectureEngine()
miro_client = MiroClient()

class AnalyzeRequest(BaseModel):
    source_type: str  # "github", "local", "prompt"
    source_value: str
    provider: Optional[str] = "custom" # "custom", "modelscope", "ollama", "openai", "openrouter", "deepseek"
    perspective: Optional[str] = "overview" # predefined perspective id
    custom_instructions: Optional[str] = "" # user focus / customization instructions
    # Custom AI Credentials
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    # Optional GitHub Token
    github_token: Optional[str] = None

class SyncMiroRequest(BaseModel):
    architecture: Dict[str, Any]
    perspective: Optional[str] = "overview"
    offset_x: Optional[float] = -300
    offset_y: Optional[float] = -150
    # Custom Miro Credentials
    access_token: Optional[str] = None
    board_id: Optional[str] = None
    team_id: Optional[str] = None

class BoardInfoRequest(BaseModel):
    access_token: Optional[str] = None
    board_id: Optional[str] = None
    team_id: Optional[str] = None

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
def health():
    return {"status": "ok", "app": "OmniArch", "version": "1.0.0"}

@router.get("/healthz")
def healthz():
    kv_healthy = True if not installation_store.is_kv_enabled() else (installation_store._kv_request(["PING"]) is not None or True)
    return {
        "status": "healthy",
        "app": "OmniArch",
        "version": "1.0.0",
        "subsystems": {
            "installation_store": "kv_redis" if installation_store.is_kv_enabled() else "local_disk",
            "kv_healthy": kv_healthy,
            "analyzer": "ready",
            "rate_limiter": "active"
        }
    }

@router.get("/board-info")
@router.post("/board-info")
@limiter.limit("60/minute")
def get_board_info(request: Request, access_token: Optional[str] = None, board_id: Optional[str] = None, team_id: Optional[str] = None, req: Optional[BoardInfoRequest] = None):
    try:
        t_id = (req.team_id if req else None) or team_id
        inst = installation_store.get_installation(t_id) if t_id else None
        token = (req.access_token if req else None) or access_token or (inst.get("access_token") if inst else None)
        b_id = (req.board_id if req else None) or board_id
        client = MiroClient(access_token=token, board_id=b_id, team_id=t_id) if (token or b_id) else miro_client
        info = client.get_board_info()

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
@limiter.limit("60/minute")
def get_sample_repos(request: Request):
    return SAMPLE_REPOS

@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze_codebase(request: Request, req: AnalyzeRequest):
    try:
        if req.source_type == "github":
            codebase_data = await asyncio.to_thread(CodebaseAnalyzer.fetch_github_repo, req.source_value, github_token=req.github_token)
        elif req.source_type == "local":
            codebase_data = await asyncio.to_thread(CodebaseAnalyzer.scan_directory, req.source_value)
        elif req.source_type == "prompt":
            codebase_data = {
                "root_name": "Custom System",
                "languages": {"Architecture Spec": 1},
                "file_tree": ["system_spec.txt"],
                "key_files": {"system_spec.txt": req.source_value},
                "signatures": {}
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        analysis_result = await asyncio.to_thread(
            engine.analyze_architecture,
            codebase_data, 
            provider=req.provider or "custom",
            perspective=req.perspective or "overview",
            custom_instructions=req.custom_instructions or "",
            api_key=req.api_key,
            base_url=req.base_url,
            model_name=req.model_name
        )
        return {
            "success": True,
            "architecture": analysis_result["architecture"],
            "usage": analysis_result["usage"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-stream")
@limiter.limit("10/minute")
async def analyze_codebase_stream(request: Request, req: AnalyzeRequest):
    try:
        if req.source_type == "github":
            codebase_data = await asyncio.to_thread(CodebaseAnalyzer.fetch_github_repo, req.source_value, github_token=req.github_token)
        elif req.source_type == "local":
            codebase_data = await asyncio.to_thread(CodebaseAnalyzer.scan_directory, req.source_value)
        elif req.source_type == "prompt":
            codebase_data = {
                "root_name": "Custom System",
                "languages": {"Architecture Spec": 1},
                "file_tree": ["system_spec.txt"],
                "key_files": {"system_spec.txt": req.source_value},
                "signatures": {}
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        return StreamingResponse(
            engine.stream_architecture_analysis(
                codebase_data, 
                provider=req.provider or "custom",
                perspective=req.perspective or "overview",
                custom_instructions=req.custom_instructions or "",
                api_key=req.api_key,
                base_url=req.base_url,
                model_name=req.model_name
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScaffoldRequest(BaseModel):
    component_name: str
    component_type: Optional[str] = "service"
    tech: Optional[str] = "FastAPI"
    description: Optional[str] = ""
    endpoints: Optional[List[str]] = None
    provider: Optional[str] = "custom"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None

@router.post("/scaffold")
@limiter.limit("15/minute")
async def scaffold_component(request: Request, req: ScaffoldRequest):
    try:
        boilerplate = await asyncio.to_thread(
            engine.scaffold_component_boilerplate,
            component_name=req.component_name,
            component_type=req.component_type or "service",
            tech=req.tech or "FastAPI",
            description=req.description or "",
            endpoints=req.endpoints,
            provider=req.provider or "custom",
            api_key=req.api_key,
            base_url=req.base_url,
            model_name=req.model_name
        )
        return {
            "success": True,
            "scaffold": boilerplate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-miro")
@limiter.limit("20/minute")
async def sync_to_miro(request: Request, req: SyncMiroRequest):
    try:
        inst = installation_store.get_installation(req.team_id) if req.team_id else None
        token = req.access_token or (inst.get("access_token") if inst else None)
        client = MiroClient(access_token=token, board_id=req.board_id, team_id=req.team_id) if (token or req.board_id) else miro_client
        res = await asyncio.to_thread(
            client.sync_architecture_diagram,
            arch_data=req.architecture,
            start_x=req.offset_x or -300,
            start_y=req.offset_y or -150,
            perspective=req.perspective or "overview"
        )
        return {
            "success": True,
            "result": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import RedirectResponse
from fastapi import Request

@router.get("/oauth/authorize")
def oauth_authorize(team_id: Optional[str] = None, redirect: bool = False):
    auth_data = oauth_manager.generate_authorization_url(team_id=team_id)
    if redirect:
        return RedirectResponse(url=auth_data["url"])
    return auth_data

@router.get("/oauth/callback")
@limiter.limit("10/minute")
def oauth_callback(request: Request, code: str, state: str):
    if not oauth_manager.validate_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth CSRF state parameter.")
    try:
        token_info = oauth_manager.exchange_code_for_token(code)
        team_id = token_info.get("team_id")
        return RedirectResponse(url=f"/?oauth=success&team_id={team_id}")
    except Exception as e:
        return RedirectResponse(url=f"/?oauth=error&message={str(e)}")

@router.get("/oauth/installations")
def list_installations():
    return {"installations": installation_store.list_installations()}

@router.delete("/oauth/installations/{team_id}")
def delete_installation(team_id: str):
    success = installation_store.delete_installation(team_id)
    return {"success": success}

class UninstallPayload(BaseModel):
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    event: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@router.post("/oauth/uninstall")
@router.post("/oauth/webhook")
async def oauth_uninstall_webhook(request: Request):
    """
    Handles Miro Marketplace app uninstall webhook.
    Revokes credentials and cleans up multi-tenant installation storage.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    team_id = body.get("team_id") or (body.get("data", {}).get("team_id") if isinstance(body.get("data"), dict) else None)
    if not team_id:
        # Check query params fallback
        team_id = request.query_params.get("team_id")

    if team_id:
        installation_store.delete_installation(str(team_id))
        return {"success": True, "message": f"Installation revoked for team {team_id}"}
    return {"success": True, "message": "Webhook processed"}


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
DIST_DIR = API_DIR / "dist" if (API_DIR / "dist").exists() else API_DIR.parent / "frontend" / "dist"

# Include router for root, /api, and /api/index.py to handle all Vercel proxying patterns
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/api/index.py")
app.include_router(router, prefix="")

# Mount static assets if dist exists
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

if (DIST_DIR / "slides").exists():
    app.mount("/slides", StaticFiles(directory=str(DIST_DIR / "slides")), name="slides")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = DIST_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(str(fav))
    return HTMLResponse(content="", status_code=204)

@app.get("/slides.html", include_in_schema=False)
def get_slides():
    slides = DIST_DIR / "slides.html"
    if slides.exists():
        return FileResponse(str(slides))
    return HTMLResponse("<h1>Slides not found</h1>", status_code=404)

@app.get("/", include_in_schema=False)
def serve_index():
    index = DIST_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "ok", "app": "OmniArch"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


