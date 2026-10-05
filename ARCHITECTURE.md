# OmniArch Technical Architecture & Execution Flow

This document provides a deep dive into the internal mechanics of OmniArch: how codebases are ingested, sanitized, analyzed via AST pattern extraction, reasoned over by multi-model AI, synchronized to Miro canvas boards, and automated via GitHub Actions.

---

## 1. System Overview

OmniArch transforms raw software codebases into interactive, production-ready system architecture diagrams. It operates as a dual-surface developer tool:
1. **Interactive Web Application & Miro Web SDK Plugin**: A fullstack application for on-demand codebase analysis, multi-perspective exploration, and bi-directional code scaffolding.
2. **Automated GitHub Action**: A continuous integration step that runs on Pull Requests, detects architectural drift, and synchronizes living diagrams to Miro.

---

## 2. End-to-End Data Flow

```mermaid
flowchart TD
    subgraph Ingestion ["1. Ingestion & Sandbox Layer"]
        A[GitHub URL / Local Directory / Text Spec] --> B[Sandbox Archive Download / Shallow Clone]
        B --> C[Noise Filter: Remove node_modules, .git, .venv, binaries]
        C --> D[File Tree Builder: Max 80 primary paths]
    end

    subgraph Analysis ["2. AST Signature Extraction & Security"]
        D --> E[Key Manifests & Entrypoint Scanner]
        E --> F[AST Pattern Extractors: Routes, Models, Clients]
        F --> G[In-Memory Secret Redaction: AWS, Stripe, JWT, DB URIs]
        G --> H[Context Assembler: ~4,000 token prompt]
    end

    subgraph Reasoning ["3. Multi-Model Inference & Streaming"]
        H --> I{AI Model Gateway}
        I -->|Primary Path| J[ModelScope / OpenAI / OpenRouter / DeepSeek / Ollama]
        J -->|Server-Sent Events| K[Live Chain-of-Thought Reasoning Stream]
        K --> L[Fault-Tolerant JSON Parser & Auto-Repair]
        I -->|Fallback on 429 / Timeout >25s| M[Deterministic AST Topological Synthesizer]
        L --> N[Normalized 5-Tier Architecture Graph]
        M --> N
    end

    subgraph Delivery ["4. Presentation & Canvas Synchronization"]
        N --> O[Interactive Web Visualizer & Reasoning Drawer]
        N --> P[Bi-Directional Code Scaffolding Generator]
        N --> Q[Miro REST API & Web SDK v2 Sync Engine]
        N --> R[GitHub Action PR Review Comment with Mermaid Preview]
    end
```

---

## 3. Deep-Dive: Ingestion & Static AST Parsing

### 3.1 Sandbox Isolation
When a GitHub repository URL is provided (`https://github.com/owner/repo`):
1. The backend (`backend/analyzer.py`) issues an authenticated or public request to download the repository archive (`.zip`) or executes a shallow clone (`git clone --depth 1`) in an isolated temporary directory (`tempfile.mkdtemp()`).
2. Operating system directories (`/etc`, `/usr`, `/System`, `/var`, `C:\Windows`) and user credentials (`.ssh`, `.aws`, `.gemini`) are strictly blocked by `is_safe_scan_path()`.

### 3.2 Noise Elimination
The scanner filters out directories and extensions that add no architectural value:
- **Ignored Directories**: `node_modules`, `.git`, `.next`, `dist`, `build`, `__pycache__`, `.venv`, `coverage`.
- **Ignored Extensions**: `.png`, `.jpg`, `.svg`, `.ico`, `.lock`, `.pyc`, `.min.js`, `.min.css`, `.map`, `.pkl`, `.parquet`, `.db`.

### 3.3 Static AST Pattern Extraction
To prevent context overflow, OmniArch does not send raw source files in bulk. Instead, regex AST extractors inspect files for structural signatures:

| Architectural Signal | Language / Framework | Extraction Regex / Pattern |
|---|---|---|
| **REST Endpoints** | FastAPI, Flask, Express, Go, Java | `@(app\|router)\.(get\|post\|put\|delete\|patch)\(['"]([^'"]+)['"]` |
| **Data Models & Schemas** | Pydantic, SQLAlchemy, Django, Prisma | `class (\w+)\((?:BaseModel\|Base\|models\.Model)\)`, `model\s+(\w+)\s+\{` |
| **Integrations & Clients** | Redis, Kafka, Celery, S3, Stripe | `(redis\.Redis\|KafkaProducer\|Celery\|boto3\.client\|stripe\.)` |

### 3.4 Automated Secret Redaction
Before any code snippet is assembled into the prompt, it passes through `redact_secrets()`, which replaces sensitive credentials with safe tokens in-memory:
- AWS Access Keys: `AKIA[0-9A-Z]{16}` -> `[REDACTED_AWS_KEY]`
- GitHub Tokens: `ghp_[0-9a-zA-Z]{36}` -> `[REDACTED_GITHUB_TOKEN]`
- OpenAI / LLM Keys: `sk-[0-9a-zA-Z]{20,}` -> `[REDACTED_OPENAI_KEY]`
- JWT Bearer Tokens: `eyJ[A-Za-z0-9-_]{10,}\...` -> `[REDACTED_JWT_TOKEN]`
- Database Connection URIs: `postgres://user:pass@host/db` -> `[REDACTED_DB_CONNECTION_STRING]`

---

## 4. Multi-Model Inference & Fail-Safe Engine

### 4.1 Universal BYOK Provider Architecture
OmniArch interfaces with any OpenAI-compatible inference endpoint via a unified client abstraction in `backend/engine.py`:
- **ModelScope Cloud**: `https://api-inference.modelscope.ai/v1` (Default model: `Qwen/Qwen3.8-27B`)
- **OpenRouter**: `https://openrouter.ai/api/v1` (`qwen/qwen-2.5-coder-32b-instruct`, `deepseek/deepseek-chat`)
- **Local Ollama**: `http://localhost:11434/v1` (`qwen2.5-coder:7b`, `llama3.2`)
- **OpenAI / Azure / Groq**: Standard OpenAI-compatible API keys and base URLs.

### 4.2 8 SDLC Perspective Directives
The prompt instructs the model to structure the diagram according to one of eight system perspectives:
1. **Overview (HLD)**: Presentation, Ingress Gateway, Core Microservices, Persistence, and External Integrations.
2. **Data Flow**: End-to-end request lifecycle from client to database and return.
3. **Database & Storage (LLD / ER)**: Entity tables, relational boundaries, caching, and connection pools.
4. **CI/CD Deployment**: Git triggers, test suites, Docker containers, registry packaging, and cloud hosting.
5. **Security & Zero-Trust**: Auth flows (JWT/OAuth), subnet boundaries, rate limiting, and RBAC.
6. **Async Workers**: Task queues (Celery/Redis), event brokers (Kafka/RabbitMQ), and scheduled jobs.
7. **Observability**: Prometheus metrics, distributed tracing, structured logging, and alerting.
8. **AI / RAG Pipeline**: Prompt routing, vector databases (Qdrant/Pinecone), LLM inference, and memory stores.

### 4.3 Robust Schema Parser & Auto-Repair
The engine sanitizes raw model completions:
1. **Thinking Tag Extraction**: Cleans `<think>` and `reasoning_content` blocks used by reasoning models (DeepSeek-R1, Qwen Thinking).
2. **Code Fence Extraction**: Extracts JSON payloads embedded inside ` ```json ... ``` ` blocks.
3. **Unclosed Bracket Repair**: Automatically counts unclosed `{` and `[` characters caused by model token limits and appends closing delimiters.
4. **Schema Normalization**: Normalizes alternate response shapes (`components`, `services`, `files`) into standard 5-layer diagram definitions.

### 4.4 Deterministic AST Topological Fallback
If an upstream AI provider is rate-limited (`429`), encounters cold-start queueing, or times out (>25s), the engine falls back to static AST synthesis:
- Discovered routes are assigned to `layer_gateway`.
- Key service files are mapped to `layer_services`.
- Discovered database models and cache clients are mapped to `layer_data`.
- Connections are inferred from file import dependency trees.

---

## 5. Miro Synchronization & Multi-Tenant OAuth2

### 5.1 OAuth2 Lifecycle & Scopes
OmniArch requests minimal OAuth2 scopes:
- `boards:read`: Validates target board existence, title, and team permissions.
- `boards:write`: Creates and modifies frame widgets, rectangular cards, sticky notes, and connectors.

### 5.2 Dynamic Redirect Negotiation
The authorization flow in `backend/oauth.py` dynamically handles redirect URIs across environments:
- Local development: `http://localhost:8000/api/oauth/callback`
- Production / Vercel: `https://<domain>/api/oauth/callback`

### 5.3 In-Place Incremental Canvas Sync
Rather than deleting and recreating shapes on every run:
1. The client queries the board for an existing frame matching the perspective title.
2. Existing widgets are matched by component identifier (`node_id`).
3. Geometry, titles, and metadata are updated in-place to preserve any user notes or manual rearrangements on the canvas.

---

## 6. GitHub Action Architecture & PR Review Engine

When OmniArch runs inside a GitHub Action (`.github/workflows/omniarch-sync.yml` or `action.yml`):

1. **Local Checkout Scan**: Ingests repository files directly from `$GITHUB_WORKSPACE`.
2. **Topological Synthesis**: Generates the complete architecture graph.
3. **Drift Detection**:
   - Calculates differences between existing Miro canvas state and current code.
   - Flags changes as `CRITICAL: ARCHITECTURE REVIEW REQUIRED` (if services/databases were added or removed) or `IN-PLACE UPDATE`.
4. **Automated PR Review Comment**:
   - Renders a native GitHub Mermaid graph directly inside the Pull Request conversation.
   - Injects a summary table of all discovered components, tech stacks, and architectural recommendations.
   - Provides deep-link URLs to jump directly to the target frame on the Miro board.

---

## 7. Security and Privacy Guarantees

- **Zero Data Retention**: Code scans and AST structures are processed transiently in-memory and discarded upon response completion.
- **Client-Side Secret Shield**: All LLM API keys and Miro access tokens configured in the browser UI are stored exclusively in client-side `localStorage` / `sessionStorage`.
- **Marketplace Webhook Compliance**: Implements `POST /api/oauth/uninstall` to immediately revoke tokens and delete stored installation records when an administrator uninstalls the application from Miro.
