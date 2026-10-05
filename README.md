# OmniArch — Universal Codebase to Miro Architecture Engine

> 🏆 **Born & Won at the [Miro x Qwen x Kramer's Community Buildathon](https://lu.ma/biyq38x0) (Hyderabad)**  
> Originally created as **QwenArch** (`qwen-arch-canvas`) to connect Alibaba Qwen with Miro's infinite canvas, OmniArch has evolved into a **Universal Living Architecture Engine & Plugin** supporting any model (Qwen, OpenAI, DeepSeek, Claude, Groq, Local Ollama) with zero lock-in and complete **BYOK (Bring Your Own Keys)** flexibility.

OmniArch bridges software codebases and visual system design. It extracts AST signatures (REST routes, models, message brokers, dependencies) with zero code retention, feeds them into your chosen reasoning LLM, and renders editable, presentation-grade C4 architecture diagrams directly on Miro boards.

---

## 🌟 The Origin & Evolution

1. **Phase 1 (The Hackathon Winner):** Built and won during the **[Miro x Qwen Meetup & Buildathon](https://lu.ma/biyq38x0)**, *QwenArch* proved that Alibaba Qwen 2.5 Coder & Qwen 3.8 could analyze whole codebases in seconds and translate them into native Miro vector shapes, sticky notes, and orthogonal connectors.
2. **Phase 2 (Universal Multi-Model Plugin):** Extended the core architecture into **OmniArch** — an open, universal plugin architecture. Developers can now plug in **any LLM provider** (ModelScope, OpenAI, DeepSeek, Anthropic Claude via OpenRouter, Groq, or private local Ollama) using standard OpenAI-compatible endpoints.
3. **Phase 3 (Enterprise BYOK & CI/CD Bot):** Added a true **BYOK (Bring Your Own Key)** model. Plug in your own Miro workspace access tokens and LLM API keys. Run via interactive in-canvas Miro Web SDK v2 or headless via our **GitHub Action** on every pull request.

---

## Key Features

- **🏆 Proven Hackathon-Winning Engine:** Engineered from the ground up for high-signal AST extraction and living architectural documentation.
- **🔌 Universal Multi-Model & BYOK:** Zero vendor lock-in. Bring your own API keys for ModelScope (Qwen), OpenAI (GPT-4o), DeepSeek (V3/R1), OpenRouter (Claude), Groq, or local Ollama.
- **8 SDLC Architectural Perspectives:** Purpose-built diagrams for HLD, Request Lifecycle, Data Model/ERD, CI/CD Pipelines, Security/Zero-Trust Auth, Async Workers, Observability/SRE, and AI/RAG Pipelines.
- **Native Miro Vector Shapes:** Creates real editable cards, shape tiers, and orthogonal connectors in Miro rather than flat static image exports.
- **Automated GitHub Action Integration:** Run on every pull request to synchronize versioned architecture frames to Miro and post live Mermaid diagram reviews on PRs.
- **Miro Web SDK v2 In-Board Panel:** Open OmniArch directly within Miro canvas sidebar panels to inspect and generate diagrams on the fly.

---

## 8 SDLC Architectural Perspectives

| Perspective | Target Audience | Primary Focus |
| :--- | :--- | :--- |
| **System Architecture (HLD)** | Engineering Teams | End-to-end component topology from client to database tiers. |
| **Request Lifecycle & API Flow** | Backend Developers | Ingress routing, middleware, controllers, and service-to-service calls. |
| **Data Model & Schema Topology** | Database & Backend Leads | Entities, relations, primary/foreign keys, cache stores, and migrations. |
| **CI/CD & DevOps Pipeline** | DevOps / Platform Engineers | Build triggers, container registries, test runners, and deployment targets. |
| **Security & Zero-Trust Auth** | Security Teams & Auditors | Identity boundaries, JWT validation, RBAC policies, and secret stores. |
| **Async Workers & Event Streams** | Distributed Systems Engineers | Message queues, background task workers, pub/sub topics, and dead-letter queues. |
| **Observability & SRE Health** | SRE & Operations | Structured telemetry, Prometheus metrics, distributed traces, and alert monitors. |
| **AI & RAG Pipeline Flow** | AI Engineers & Data Scientists | Vector databases, embeddings, chunking, retrieval chains, and LLM reasoning steps. |

---

## GitHub Action Usage

Add the following workflow file to your repository at `.github/workflows/architecture-sync.yml`:

```yaml
name: OmniArch Architecture Sync

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  sync-architecture:
    name: Generate Architecture to Miro Canvas
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Codebase
        uses: actions/checkout@v4

      - name: Run OmniArch Visual Architecture Sync
        uses: rpavani1998/omniarch@v1.0.0
        with:
          miro-access-token: ${{ secrets.MIRO_ACCESS_TOKEN }}
          miro-board-id: ${{ secrets.MIRO_BOARD_ID }}
          perspective: 'overview'
          custom-instructions: 'Highlight public API endpoints and database trust boundaries'
          ai-provider: 'custom'
          ai-base-url: 'https://api.openai.com/v1'
          ai-model-name: 'gpt-4o'
          ai-api-key: ${{ secrets.AI_API_KEY }}
```

### Action Inputs

| Input | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `miro-access-token` | Miro OAuth Access Token with `boards:write` permissions | **Yes** | - |
| `miro-board-id` | Target Miro Board ID (e.g., `uXjVEekRCSA=`) | **Yes** | - |
| `perspective` | Architectural perspective (`overview`, `data_flow`, `database_storage`, `devops_pipeline`, `security_auth`, `async_workers`, `observability`, `ai_rag`) | No | `overview` |
| `custom-instructions`| Extra comments or team directives (e.g., 'detail Redis cache TTL') | No | `""` |
| `ai-provider` | Provider type: `custom`, `openai`, `deepseek`, `modelscope`, `openrouter`, or `ollama` | No | `custom` |
| `ai-api-key` | API Key for your chosen LLM provider | No | `""` |
| `ai-base-url` | OpenAI-compatible Base URL endpoint | No | `https://api.openai.com/v1` |
| `ai-model-name` | Model name (e.g. `gpt-4o`, `deepseek-chat`, `Qwen/Qwen3.8-27B`, `claude-3-5-sonnet`) | No | `gpt-4o` |

---

## Universal Model Compatibility (Plug & Play Any LLM)

OmniArch works with **any OpenAI-compatible API endpoint**. You only need to supply your Endpoint Base URL, API Key, and Model Name:

| Provider | Base URL (`AI_BASE_URL`) | Recommended Model (`AI_MODEL_NAME`) |
| :--- | :--- | :--- |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini`, `o1` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` |
| **ModelScope / Qwen** | `https://api-inference.modelscope.ai/v1` | `Qwen/Qwen3.8-27B`, `Qwen/Qwen2.5-Coder-32B` |
| **OpenRouter / Claude** | `https://openrouter.ai/api/v1` | `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| **Local Ollama** | `http://localhost:11434/v1` | `qwen2.5-coder:7b`, `llama3.2`, `deepseek-r1` |
| **Self-Hosted vLLM** | `http://your-server:8000/v1` | Custom hosted model ID |

---

## Local Development

```bash
# 1. Clone repository
git clone https://github.com/rpavani1998/omniarch.git
cd omniarch

# 2. Start FastAPI Backend
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 3. Start React Frontend
cd ../frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to open the application.

---

## Deployment & Hosting Guide

### Deploying to Vercel (Serverless Marketplace Backend)

OmniArch is pre-configured for zero-maintenance Vercel serverless deployment:

1. **Push your repository to GitHub** (on main or your release branch).
2. **Import project into [Vercel](https://vercel.com)**:
   - Root Directory: `./`
   - Framework Preset: **Vite**
   - Build Command: `npm run build --prefix frontend && cp -r frontend/dist api/dist`
   - Output Directory: `frontend/dist`
3. **Configure Environment Variables in Vercel Dashboard** (`Settings > Environment Variables`):
   ```env
   # Miro Marketplace OAuth Credentials
   MIRO_CLIENT_ID=your_miro_client_id
   MIRO_CLIENT_SECRET=your_miro_client_secret
   MIRO_REDIRECT_URI=https://your-domain.vercel.app/api/oauth/callback

   # Multi-Tenant Installation Storage (Vercel KV or Upstash Redis)
   KV_REST_API_URL=https://your-kv-instance.upstash.io
   KV_REST_API_TOKEN=your_kv_token

   # Default AI Inference Provider (For users without custom BYOK keys)
   AI_PROVIDER=custom
   AI_BASE_URL=https://api.openai.com/v1
   AI_MODEL_NAME=gpt-4o
   AI_API_KEY=sk-...
   ```
4. **Click Deploy**. Vercel will host your static frontend at `/` and route all API calls through serverless Python functions in `/api`.

---

## Miro Developer Portal Setup (Creating the Marketplace App)

To publish OmniArch or use it in your Miro workspace:

1. Go to **[Miro Developer Portal](https://developers.miro.com/)** and click **Create new app**.
2. **App Details:**
   - **App Name:** OmniArch — Living Codebase Architecture Engine
   - **Description:** AI-powered visual architecture diagrams from any GitHub repository directly into Miro.
3. **App URL & Embedding:**
   - **App URL:** `https://your-domain.vercel.app`
   - Under **App Capabilities**, enable **Web SDK** and check **Open in board sidebar**.
4. **OAuth2 Redirect URI:**
   - Add: `https://your-domain.vercel.app/api/oauth/callback`
5. **Permissions & Scopes:**
   - `boards:read` (Read board metadata and inspect existing shapes for in-place diffing)
   - `boards:write` (Create and update shape cards, frames, and connector lines)
6. **App Webhooks (Uninstall / Token Revocation):**
   - Webhook URL: `https://your-domain.vercel.app/api/oauth/uninstall`
   - Event subscription: `app.uninstalled`

---

## End-User Guide (How People Use OmniArch on Miro)

### Step 1: Install the App
Users visit the Miro Marketplace (or click your OAuth install URL `https://your-domain.vercel.app/api/oauth/authorize`), choose their Miro team workspace, and grant permission with 1 click.

### Step 2: Open OmniArch in Any Miro Board
1. Open any Miro board in your workspace.
2. In the left or bottom board toolbar, click the **OmniArch** icon.
3. The interactive sidebar panel opens directly on the canvas.

### Step 3: Provide Your Codebase Source
Choose from 3 input modes:
- **Public GitHub Repository:** Paste any repo URL (e.g. `https://github.com/fastapi/fastapi` or `username/repo`).
- **Local Directory / Monorepo:** Point to any local project path for AST extraction.
- **Custom Architecture Specification:** Paste a text prompt or microservices list.

### Step 4: Choose Architectural Perspective
Select from 8 purpose-built SDLC perspectives:
- `System Architecture (HLD)`
- `Request Lifecycle & API Flow`
- `Data Model & Schema Topology`
- `CI/CD & DevOps Pipeline`
- `Security & Zero-Trust Auth`
- `Async Task Queues & Workers`
- `Observability & SRE Health`
- `AI & RAG Pipeline Flow`

### Step 5: (Optional) Bring Your Own Model (BYOK)
In the Model Settings drawer, users can choose their preferred LLM (OpenAI, DeepSeek, Qwen/ModelScope, Anthropic Claude, or local Ollama) and supply their own API key. If omitted, the app uses the server default.

### Step 6: Sync to Miro Canvas
Click **Generate & Sync to Miro**.
- OmniArch analyzes the AST signatures and extracts services, databases, and gateways.
- A dedicated **non-overlapping Frame** is created on the Miro board containing color-coded cards, Sugiyama layered tiers, and orthogonal connector lines.
- Multiple perspectives sit side-by-side on the same board with generous 5500px spacing corridors.

### Step 7: Automatic In-Place PR Updates
When code is modified or a new PR is merged:
- Re-running the sync inspects existing cards on the board and performs **in-place `PATCH` updates**.
- Existing shape IDs, comments, and sticky notes are preserved without clearing or duplicating the canvas.
- Newly added microservices are added incrementally; deleted components are pruned.

### Step 8: Code Scaffolding
Click **Scaffold Code** on any shape card on the canvas or sidebar to generate runnable boilerplate implementations (FastAPI, Go, Next.js, Dockerfiles) for that component.

---

## Running Automated Tests

```bash
python3 -m unittest discover -s tests -v
```

---

## License & Compliance

- **License:** MIT License
- **Privacy Policy:** [PRIVACY.md](PRIVACY.md) / [privacy.html](https://qwenarch-canvas.vercel.app/privacy.html) (Zero codebase storage, 100% ephemeral processing)
- **Terms of Service:** [TERMS.md](TERMS.md) / [terms.html](https://qwenarch-canvas.vercel.app/terms.html)
- **Marketplace Submission Manifest:** [MARKETPLACE_SUBMISSION.md](MARKETPLACE_SUBMISSION.md)

