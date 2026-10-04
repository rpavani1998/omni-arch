# OmniArch — Universal Codebase to Miro Architecture Engine

OmniArch analyzes software repositories with **multi-model code reasoning LLMs (Qwen, DeepSeek, OpenAI, Claude, Local Ollama)** and automatically maps live, editable system architecture diagrams into **Miro's infinite whiteboard canvas**.

---

## Key Features

- **8 SDLC Architectural Perspectives:** Generates purpose-built diagrams for HLD, Request Lifecycle, Data Model/ERD, CI/CD Pipelines, Security/Zero-Trust Auth, Async Workers, Observability/SRE, and AI/RAG Pipelines.
- **Native Miro Vector Shapes:** Creates real editable cards, shape tiers, and orthogonal connectors in Miro rather than flat static image exports.
- **Multi-Model & BYOK (Bring Your Own Key):** Zero server lock-in. Connect ModelScope (Qwen), OpenAI, Anthropic, DeepSeek, or local Ollama instances.
- **Automated GitHub Action Integration:** Run on every pull request or release tag to synchronize versioned architecture frames directly to your team's Miro board.
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
        uses: rpavani1998/qwen-arch-canvas@v1.0.0
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
git clone https://github.com/rpavani1998/qwen-arch-canvas.git
cd qwen-arch-canvas

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

## One-Click Vercel Deployment

1. Connect your repository to Vercel or deploy using the Vercel CLI.
2. Under **Project Settings > Environment Variables**, configure:
   - `MIRO_ACCESS_TOKEN` : Your Miro OAuth token (`eyJ...`)
   - `MIRO_BOARD_ID` : Your target Miro Board ID (e.g. `uXjVEekRCSA=`)
   - `AI_API_KEY` : Your model provider API key
   - `AI_BASE_URL` : Provider base URL (e.g. `https://api.openai.com/v1` or `https://api.deepseek.com/v1`)
   - `AI_MODEL_NAME` : Model name (e.g. `gpt-4o` or `deepseek-chat`)
3. Click **Deploy**.

---

## Running Automated Tests

```bash
python3 -m unittest discover -s tests -v
```

---

## License & Compliance

- **License:** MIT License
- **Privacy Policy:** [privacy.html](https://qwenarch-canvas.vercel.app/privacy.html) (Zero codebase storage, 100% BYOK)
- **Terms of Service:** [terms.html](https://qwenarch-canvas.vercel.app/terms.html)
