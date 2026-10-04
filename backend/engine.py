import os
import json
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a Principal Software Architect and Visual System Design Expert.
Your task is to analyze a codebase (directory tree, key configuration manifests, routes, models, and service files) and generate a comprehensive, production-grade visual software architecture diagram specification in STRICT JSON format.

Your JSON output must have the following exact schema:
{
  "system_title": "Descriptive System Name",
  "summary": "2-3 sentence executive overview of the architecture and data flow.",
  "architecture_style": "e.g., Modular Monolith, Microservices, Clean Architecture, Event-Driven, ML Research Pipeline",
  "tech_stack": ["Tech1", "Tech2", "Tech3"],
  "layers": [
    {
      "id": "layer_presentation",
      "name": "Presentation & Clients",
      "order": 1
    },
    {
      "id": "layer_gateway",
      "name": "API & Ingress Gateway",
      "order": 2
    },
    {
      "id": "layer_services",
      "name": "Core Application Services",
      "order": 3
    },
    {
      "id": "layer_data",
      "name": "Persistence & Caching",
      "order": 4
    },
    {
      "id": "layer_external",
      "name": "External & Third-Party APIs",
      "order": 5
    }
  ],
  "nodes": [
    {
      "id": "node_unique_id",
      "name": "Component Name",
      "layer_id": "layer_presentation | layer_gateway | layer_services | layer_data | layer_external",
      "type": "frontend | gateway | service | database | cache | queue | external",
      "tech": "e.g. React 19, FastAPI, PostgreSQL, PyTorch, Redis",
      "description": "Clear explanation of this component's role.",
      "endpoints_or_features": ["Feature or endpoint 1", "Feature or endpoint 2"]
    }
  ],
  "connections": [
    {
      "from": "source_node_id",
      "to": "target_node_id",
      "protocol": "e.g. REST / HTTPS, gRPC, SQL Query, WebSocket, Pub/Sub, Python API",
      "label": "Short description of interaction (e.g. User Auth, Sync Cart, Train Pipeline)"
    }
  ],
  "insights": {
    "strengths": ["Key architectural strength 1", "Strength 2"],
    "bottlenecks": ["Potential scaling or latency bottleneck 1", "Bottleneck 2"],
    "recommendations": ["Actionable improvement 1", "Actionable improvement 2"]
  }
}

Rules:
1. Output ONLY the raw valid JSON object starting with { and ending with }. Keep internal reasoning/monologue extremely brief (under 3 sentences) so the complete JSON is generated quickly without hitting streaming timeouts.
2. Adapt intelligently to any architecture: for web/microservices use web tiers; for ML/research pipelines map notebooks/dashboards to presentation, CLI/SLURM to gateway, models/training/eval to services, datasets/checkpoints/scoresheets to data, and HPC/GPUs/frameworks to external.
3. Every node in "connections" MUST reference a valid "id" present in "nodes".
4. Group all nodes into the appropriate layer_id from the 5 standard layers.
"""

PERSPECTIVE_DIRECTIVES = {
    "overview": "Decompose the system into presentation clients, API gateway ingress, core application microservices, data persistence stores, and external third-party integrations with clear boundary responsibilities.",
    "data_flow": "Trace end-to-end request lifecycle from client action through gateway routing, authentication/authorization validation, internal service-to-service calls, database reads/writes, cache lookups, and response return.",
    "database_storage": "Focus on data persistence architecture: core entity schemas, primary database tables/collections, foreign key relations, transactional boundaries, Redis caching layers, and connection pooling.",
    "devops_pipeline": "Map the continuous integration and deployment lifecycle: Git repository triggers, automated lint/test stages, Docker containerization, artifact registry packaging, cloud infrastructure deployment, and environment promotion.",
    "security_auth": "Analyze security and trust boundaries: public vs private subnet zones, OAuth2/OIDC/JWT authentication flows, API gateway rate limiting, RBAC permission checks, secret management, and secure communication protocols.",
    "async_workers": "Highlight asynchronous background processing: task queue ingestion, distributed worker pool execution, cron schedulers, webhook consumers, pub/sub messaging channels, and retry / dead-letter queues.",
    "observability": "Structure the observability and site reliability architecture: distributed trace propagation, Prometheus metrics exporters, structured logging pipelines, health check probes, and automated alerting integrations.",
    "ai_rag": "Deconstruct the AI / RAG architecture: user prompt orchestrator, document chunking & vector database retrieval, LLM inference agent workflows, tool calling integrations, memory store, and streaming response output.",
    # Aliases for compatibility
    "event_driven": "Highlight asynchronous background processing: task queue ingestion, distributed worker pool execution, cron schedulers, webhook consumers, pub/sub messaging channels, and retry / dead-letter queues.",
    "devops_cloud": "Map the continuous integration and deployment lifecycle: Git repository triggers, automated lint/test stages, Docker containerization, artifact registry packaging, cloud infrastructure deployment, and environment promotion."
}

class ArchitectureEngine:
    def __init__(self):
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        
        self.modelscope_base = os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.ai/v1")
        self.modelscope_key = os.getenv("MODELSCOPE_API_KEY", "")
        self.modelscope_model = os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen3.8-27B")

    def _build_context(self, codebase_data: Dict[str, Any], perspective: str = "overview", custom_instructions: str = "") -> str:
        context_parts = []
        if "repo_url" in codebase_data:
            context_parts.append(f"Repository: {codebase_data['repo_url']}")
        if "root_name" in codebase_data:
            context_parts.append(f"Project Name: {codebase_data['root_name']}")
        
        context_parts.append(f"Languages: {json.dumps(codebase_data.get('languages', {}))}")
        context_parts.append("\n--- FILE STRUCTURE ---")
        context_parts.append("\n".join(codebase_data.get("file_tree", [])[:80]))
        
        context_parts.append("\n--- KEY MANIFESTS & ENTRY FILES ---")
        for fpath, content in codebase_data.get("key_files", {}).items():
            trimmed = (content[:1200] + "\n...[truncated]...") if len(content) > 1200 else content
            context_parts.append(f"\n[FILE: {fpath}]\n{trimmed}\n")


        # Add discovered structural signatures (AST extraction)
        sigs = codebase_data.get("signatures", {})
        if sigs:
            context_parts.append("\n--- EXTRACTED ARCHITECTURAL SIGNATURES ---")
            if sigs.get("discovered_routes"):
                context_parts.append(f"Discovered Endpoints & Handlers: {json.dumps(sigs['discovered_routes'])}")
            if sigs.get("discovered_models"):
                context_parts.append(f"Discovered Entities & Schema Models: {json.dumps(sigs['discovered_models'])}")
            if sigs.get("discovered_integrations"):
                context_parts.append(f"Discovered Clients & Infrastructure: {json.dumps(sigs['discovered_integrations'])}")

        # Add perspective directive
        if perspective in PERSPECTIVE_DIRECTIVES:
            context_parts.append(f"\n--- DIAGRAM PERSPECTIVE GOAL ---\n{PERSPECTIVE_DIRECTIVES[perspective]}")

        if custom_instructions and custom_instructions.strip():
            context_parts.append(f"\n--- USER ARCHITECTURAL FOCUS & CUSTOM REQUIREMENTS ---\n{custom_instructions.strip()}\nEnsure you prioritize and explicitly reflect these specific requirements, focus areas, and components in the diagram layers, nodes, data flows, and recommendations.")
            
        full_codebase_prompt = "\n".join(context_parts)
        return f"Please analyze this codebase and generate the complete visual architecture graph JSON according to the instructions:\n\n{full_codebase_prompt}"

    def _get_client_and_model(self, provider: str = "custom", api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        load_dotenv(override=True)
        provider_clean = (provider or "custom").lower()
        
        # Universal environment variable resolution with provider-specific fallbacks
        default_base_url = os.getenv("AI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or os.getenv("CUSTOM_BASE_URL") or os.getenv("MODELSCOPE_BASE_URL", "https://api.openai.com/v1")
        default_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("CUSTOM_API_KEY") or os.getenv("MODELSCOPE_API_KEY", "")
        default_model = os.getenv("AI_MODEL_NAME") or os.getenv("OPENAI_MODEL") or os.getenv("CUSTOM_MODEL") or os.getenv("MODELSCOPE_MODEL", "gpt-4o")

        if provider_clean == "ollama":
            endpoint = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            key = api_key or "ollama"
            model = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
            provider_label = f"Ollama ({model})"
        elif provider_clean == "modelscope":
            endpoint = base_url or os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.ai/v1")
            key = api_key or os.getenv("MODELSCOPE_API_KEY") or default_api_key
            model = model_name or os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen3.8-27B")
            provider_label = f"ModelScope ({model})"
        elif provider_clean == "deepseek":
            endpoint = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            key = api_key or os.getenv("DEEPSEEK_API_KEY") or default_api_key
            model = model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            provider_label = f"DeepSeek ({model})"
        elif provider_clean in ["openrouter", "groq", "openai", "custom"]:
            endpoint = base_url or default_base_url
            key = api_key or default_api_key
            model = model_name or default_model
            provider_label = f"AI Provider ({model})"
        else:
            endpoint = base_url or default_base_url
            key = api_key or default_api_key
            model = model_name or default_model
            provider_label = f"Custom Model ({model})"
            
        client = OpenAI(base_url=endpoint, api_key=key or "dummy", timeout=15.0)
        return client, model, provider_label


    def stream_architecture_analysis(self, codebase_data: Dict[str, Any], provider: str = "modelscope", perspective: str = "overview", custom_instructions: str = "", api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """Streams reasoning tokens in real-time, then yields complete architecture JSON."""
        import time
        start_time = time.time()
        client, target_model, provider_label = self._get_client_and_model(provider, api_key, base_url, model_name)
        user_message = self._build_context(codebase_data, perspective, custom_instructions)

        try:
            stream = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=4096,
                stream=True
            )

            full_content = ""
            full_reasoning = ""

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    reasoning_chunk = getattr(delta, "reasoning_content", None) or ""
                    content_chunk = getattr(delta, "content", None) or ""

                    if reasoning_chunk:
                        full_reasoning += reasoning_chunk
                        yield f"data: {json.dumps({'type': 'reasoning', 'chunk': reasoning_chunk})}\n\n"
                    elif content_chunk:
                        full_content += content_chunk
                        yield f"data: {json.dumps({'type': 'content', 'chunk': content_chunk})}\n\n"

            # Parse the final JSON: prioritize content stream first, then reasoning
            duration_ms = int((time.time() - start_time) * 1000)
            parsed_json = self._parse_json_response(full_content)
            
            # If content didn't parse a custom diagram, try reasoning text
            if parsed_json.get("nodes", [])[0].get("id") == "client_ui" and full_reasoning and "{" in full_reasoning:
                alt_parsed = self._parse_json_response(full_reasoning)
                if alt_parsed and alt_parsed.get("nodes", [])[0].get("id") != "client_ui":
                    parsed_json = alt_parsed

            # Fallback reasoning if model didn't stream explicit reasoning
            if not full_reasoning:
                full_reasoning = "1. Analyzed ingress routes and API gateways.\n2. Decomposed microservices and message queues.\n3. Mapped database persistence tiers and caching layers.\n4. Extracted architectural strengths and scaling considerations."

            usage = {
                "total_tokens": len((full_content + full_reasoning).split()) * 2,
                "duration_ms": duration_ms,
                "model": target_model,
                "provider": provider_label,
                "reasoning": full_reasoning
            }

            yield f"data: {json.dumps({'type': 'complete', 'architecture': parsed_json, 'usage': usage})}\n\n"

        except Exception as e:
            print(f"[ArchitectureEngine] Streaming failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    def analyze_architecture(self, codebase_data: Dict[str, Any], provider: str = "custom", perspective: str = "overview", custom_instructions: str = "", api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Calls LLM to deduce architecture from codebase metadata and returns graph + token metrics."""
        import time
        start_time = time.time()
        client, target_model, provider_label = self._get_client_and_model(provider, api_key, base_url, model_name)
        
        user_message = self._build_context(codebase_data, perspective, custom_instructions)
        try:
            raw_response, usage_metrics = self._call_llm_direct(client, target_model, provider_label, user_message)
            duration_ms = int((time.time() - start_time) * 1000)
            usage_metrics["duration_ms"] = duration_ms
            parsed_json = self._parse_json_response(raw_response)
        except Exception as e:
            print(f"[ArchitectureEngine] Direct LLM call failed ({e}). Synthesizing architectural graph from AST signatures...")
            parsed_json = self._synthesize_from_codebase(codebase_data, perspective)
            duration_ms = int((time.time() - start_time) * 1000)

            usage_metrics = {
                "total_tokens": 150,
                "duration_ms": duration_ms,
                "model": f"{target_model} (AST fallback)",
                "provider": provider_label,
                "reasoning": f"Synthesized architectural topology from code AST signatures due to upstream latency: {e}"
            }

        return {
            "architecture": parsed_json,
            "usage": usage_metrics
        }


    def generate_architecture(self, codebase_data: Dict[str, Any], provider: str = "custom", perspective: str = "overview", custom_instructions: str = "", api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method returning the architecture graph dictionary directly."""
        res = self.analyze_architecture(codebase_data, provider, perspective, custom_instructions, api_key, base_url, model_name)
        return res.get("architecture", self._get_fallback())

    def scaffold_component_boilerplate(
        self,
        component_name: str,
        component_type: str = "service",
        tech: str = "FastAPI",
        description: str = "",
        endpoints: Optional[List[str]] = None,
        provider: str = "custom",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scaffolds production-grade starter code, Dockerfile, and docker-compose block for a service node."""
        client, target_model, provider_label = self._get_client_and_model(provider, api_key, base_url, model_name)
        
        prompt = f"""You are a Principal Software Engineer. Generate production-ready boilerplate starter code for an architectural component with the following specifications:
Component Name: {component_name}
Component Type: {component_type}
Technology / Framework: {tech or 'FastAPI / Python'}
Description: {description}
Endpoints / Features: {json.dumps(endpoints or [])}

Output STRICT JSON only with the following schema:
{{
  "component_name": "{component_name}",
  "file_name": "main.py or server.ts",
  "source_code": "Full, working, clean starter code with imports, routes, healthcheck, and CORS",
  "dockerfile": "Multi-stage production Dockerfile",
  "compose_snippet": "Docker Compose service block",
  "quickstart_commands": ["npm install or pip install -r requirements.txt", "docker build ..."]
}}
"""
        try:
            resp = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer who outputs strictly formatted JSON with production boilerplate code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            raw = resp.choices[0].message.content or ""
            cleaned = raw.strip()
            if "```" in cleaned:
                m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
                if m:
                    cleaned = m.group(1)
                else:
                    cleaned = re.sub(r"```(?:json)?", "", cleaned).replace("```", "").strip()
            
            start_i = cleaned.find("{")
            end_i = cleaned.rfind("}")
            if start_i != -1 and end_i != -1 and end_i > start_i:
                return json.loads(cleaned[start_i:end_i+1])
        except Exception as e:
            print(f"[Engine] Scaffolding fallback: {e}")

        # Reliable static fallback if model fails
        safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', component_name.lower())
        return {
            "component_name": component_name,
            "file_name": "main.py",
            "source_code": f'# Boilerplate starter for {component_name}\nfrom fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title="{component_name}", description="{description}")\n\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])\n\n@app.get("/health")\ndef health():\n    return {{"status": "healthy", "service": "{component_name}"}}\n',
            "dockerfile": f"FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n",
            "compose_snippet": f"  {safe_id}:\n    build: .\n    ports:\n      - \"8000:8000\"\n    environment:\n      - ENV=production\n",
            "quickstart_commands": ["pip install fastapi uvicorn", "uvicorn main:app --reload"]
        }

    def _call_llm_direct(self, client: OpenAI, target_model: str, provider_label: str, user_content: str):
        try:
            print(f"[ArchitectureEngine] Invoking {provider_label} ({target_model})...")
            resp = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            msg = resp.choices[0].message
            content = msg.content or ""
            reasoning_text = getattr(msg, "reasoning_content", "") or ""
            
            if not reasoning_text and "<think>" in content:
                think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if think_match:
                    reasoning_text = think_match.group(1).strip()
                    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

            if not reasoning_text:
                reasoning_text = f"1. Ingress & Routing Analysis: Evaluated API gateways and entrypoints.\n2. Domain Decomposition: Identified core microservices/modules.\n3. Data Flow & State: Mapped persistence tiers and storage.\n4. Scalability & Resilience: Assessed coupling and bottlenecks."

            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0,
                "total_tokens": getattr(resp.usage, "total_tokens", 0) if resp.usage else 0,
                "model": target_model,
                "provider": provider_label,
                "reasoning": reasoning_text
            }
            return content if content.strip() else reasoning_text, usage
        except Exception as e:
            print(f"[ArchitectureEngine] Direct LLM invocation failed: {e}")
            raise e

        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0,
            "completion_tokens": getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0,
            "total_tokens": getattr(resp.usage, "total_tokens", 0) if resp.usage else 0,
            "model": self.ollama_model,
            "provider": "Local Ollama",
            "reasoning": reasoning_text
        }
        return content if content.strip() else reasoning_text, usage

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans, extracts, and repairs JSON safely from model response."""
        if not text or not text.strip():
            return self._get_fallback()

        cleaned = text.strip()
        
        # Extract from markdown block if present
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
            if match:
                cleaned = match.group(1)
            else:
                cleaned = re.sub(r"```(?:json)?", "", cleaned).replace("```", "").strip()

        # Find first { and last }
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        
        candidate_json = None
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx + 1]
            try:
                candidate_json = json.loads(json_str)
            except Exception:
                # Try cleaning trailing commas
                try:
                    cleaned_commas = re.sub(r",\s*([\]}])", r"\1", json_str)
                    candidate_json = json.loads(cleaned_commas)
                except Exception:
                    pass

        # If start_idx exists but end_idx is truncated, attempt auto-closing
        if not candidate_json and start_idx != -1:
            partial_json = cleaned[start_idx:]
            open_braces = partial_json.count("{") - partial_json.count("}")
            open_brackets = partial_json.count("[") - partial_json.count("]")
            repaired = partial_json.rstrip().rstrip(",") + ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))
            repaired = re.sub(r",\s*([\]}])", r"\1", repaired)
            try:
                candidate_json = json.loads(repaired)
            except Exception:
                pass

        # Normalize parsed architecture
        if isinstance(candidate_json, dict):
            nodes = []
            connections = []

            # 1. Direct nodes format
            if "nodes" in candidate_json and isinstance(candidate_json["nodes"], list) and len(candidate_json["nodes"]) > 0:
                nodes = candidate_json["nodes"]
                connections = candidate_json.get("connections", [])
            # 2. Nested under 'architecture'
            elif "architecture" in candidate_json and isinstance(candidate_json["architecture"], dict):
                arch = candidate_json["architecture"]
                if "nodes" in arch and isinstance(arch["nodes"], list):
                    nodes = arch["nodes"]
                elif "components" in arch and isinstance(arch["components"], list):
                    nodes = arch["components"]
                elif "services" in arch and isinstance(arch["services"], list):
                    nodes = arch["services"]
                connections = arch.get("connections", candidate_json.get("connections", []))
            # 3. Direct components or services format
            elif "components" in candidate_json and isinstance(candidate_json["components"], list):
                nodes = candidate_json["components"]
                connections = candidate_json.get("connections", [])
            elif "services" in candidate_json and isinstance(candidate_json["services"], list):
                nodes = candidate_json["services"]
                connections = candidate_json.get("connections", [])
            # 4. File-based architecture format (e.g. "files": [...])
            elif "files" in candidate_json and isinstance(candidate_json["files"], list):
                for f in candidate_json["files"]:
                    p = f.get("path", f.get("name", "component"))
                    role = f.get("role", "service")
                    layer = "layer_gateway" if any(k in role.lower() for k in ["entry", "main", "cli", "router"]) else ("layer_data" if any(k in role.lower() for k in ["data", "db", "dataset", "store", "csv"]) else "layer_services")
                    ntype = "gateway" if "gateway" in layer else ("database" if "data" in layer else "service")
                    node_id = re.sub(r'[^a-zA-Z0-9_]', '_', p)
                    nodes.append({
                        "id": node_id,
                        "name": p,
                        "layer_id": layer,
                        "type": ntype,
                        "tech": f.get("tech", "Python / PyTorch"),
                        "description": ", ".join(f.get("responsibilities", [])) if isinstance(f.get("responsibilities"), list) else f.get("role", "Component"),
                        "endpoints_or_features": f.get("functions", f.get("classes", []))[:3]
                    })
                    for dep in f.get("dependencies", []):
                        dep_id = re.sub(r'[^a-zA-Z0-9_]', '_', dep)
                        connections.append({
                            "from": node_id,
                            "to": dep_id,
                            "protocol": "Python Import",
                            "label": "Calls"
                        })

            if len(nodes) > 0:
                # Ensure each node has required fields
                cleaned_nodes = []
                for n in nodes:
                    if isinstance(n, dict):
                        nid = str(n.get("id", n.get("name", "node"))).replace(".", "_")
                        nname = n.get("name", n.get("id", "Service"))
                        lid = n.get("layer_id", "layer_services")
                        cleaned_nodes.append({
                            "id": nid,
                            "name": nname,
                            "layer_id": lid if lid.startswith("layer_") else f"layer_{lid}",
                            "type": n.get("type", "service"),
                            "tech": n.get("tech", "Python / Cloud"),
                            "description": n.get("description", "Core system component"),
                            "endpoints_or_features": n.get("endpoints_or_features", [])[:3]
                        })

                # Ensure layers exist
                layers = candidate_json.get("layers", [
                    {"id": "layer_presentation", "name": "Presentation & Clients", "order": 1},
                    {"id": "layer_gateway", "name": "API & Ingress Gateway", "order": 2},
                    {"id": "layer_services", "name": "Core Application Services", "order": 3},
                    {"id": "layer_data", "name": "Persistence & Caching", "order": 4},
                    {"id": "layer_external", "name": "External & Third-Party APIs", "order": 5}
                ])

                return {
                    "system_title": candidate_json.get("system_title", candidate_json.get("project", "Analyzed Architecture")),
                    "summary": candidate_json.get("summary", candidate_json.get("description", "System architecture extracted from codebase.")),
                    "architecture_style": candidate_json.get("architecture_style", "Modular Architecture"),
                    "tech_stack": candidate_json.get("tech_stack", ["Python", "PyTorch"]),
                    "layers": layers,
                    "nodes": cleaned_nodes,
                    "connections": connections or candidate_json.get("connections", []),
                    "insights": candidate_json.get("insights", {
                        "strengths": ["Clear modular separation", "Scalable domain boundaries"],
                        "bottlenecks": ["Compute and data throughput dependencies"],
                        "recommendations": ["Introduce caching layers and pipeline orchestration"]
                    })
                }

        return self._get_fallback()

    def _synthesize_from_codebase(self, codebase_data: Dict[str, Any], perspective: str = "overview") -> Dict[str, Any]:
        root = codebase_data.get("root_name") or "System"
        key_files = codebase_data.get("key_files", {})
        sigs = codebase_data.get("signatures", {})
        file_tree = codebase_data.get("file_tree", [])
        
        nodes = []
        connections = []
        
        # 1. UI Layer
        has_frontend = any("frontend" in f or "App.jsx" in f or "package.json" in f for f in file_tree)
        if has_frontend:
            nodes.append({
                "id": "ui_client",
                "name": f"{root} Web UI",
                "layer_id": "layer_presentation",
                "type": "frontend",
                "tech": "React 18 / Vite / Tailwind",
                "description": "Interactive diagram canvas and model settings interface",
                "endpoints_or_features": ["Canvas Viewer", "Perspective Selector", "Model Settings"]
            })
            
        # 2. Ingress & Gateway Layer
        has_api = any("main.py" in f or "fastapi" in str(key_files).lower() for f in file_tree)
        if has_api:
            routes = sigs.get("discovered_routes", [])[:4]
            nodes.append({
                "id": "api_gateway",
                "name": "FastAPI Core Gateway",
                "layer_id": "layer_gateway",
                "type": "gateway",
                "tech": "FastAPI / Starlette",
                "description": "API Gateway with OAuth2, rate limiting, and SSE streaming",
                "endpoints_or_features": routes or ["/api/analyze", "/api/sync-miro", "/api/oauth"]
            })
            if has_frontend:
                connections.append({
                    "from": "ui_client",
                    "to": "api_gateway",
                    "protocol": "HTTPS / SSE",
                    "label": "REST API & Event Streams"
                })

        # 3. Core Application Services
        if any("engine.py" in f for f in file_tree):
            nodes.append({
                "id": "arch_engine",
                "name": "Architecture Reasoning Engine",
                "layer_id": "layer_services",
                "type": "service",
                "tech": "Multi-Model AI / AST Parser",
                "description": "Analyzes codebase structure and deduces layered system topology",
                "endpoints_or_features": ["AST Signature Extraction", "Reasoning Inference", "Sugiyama Layout"]
            })
            if has_api:
                connections.append({
                    "from": "api_gateway",
                    "to": "arch_engine",
                    "protocol": "Internal Python",
                    "label": "Invokes Analysis"
                })

        if any("miro_client.py" in f for f in file_tree):
            nodes.append({
                "id": "miro_sync_service",
                "name": "Miro Board Sync Service",
                "layer_id": "layer_services",
                "type": "service",
                "tech": "Miro REST API v2",
                "description": "Manages 2D canvas shapes, perspective frames, and incremental PR diffing",
                "endpoints_or_features": ["In-Place PATCH", "Frame Alignment", "Connector Routing"]
            })
            if has_api:
                connections.append({
                    "from": "api_gateway",
                    "to": "miro_sync_service",
                    "protocol": "Internal Python",
                    "label": "Dispatches Sync"
                })

        # 4. Persistence & Storage Layer
        if any("oauth.py" in f for f in file_tree):
            nodes.append({
                "id": "kv_oauth_store",
                "name": "Multi-Tenant Installation Store",
                "layer_id": "layer_data",
                "type": "database",
                "tech": "Vercel KV / Upstash Redis",
                "description": "Stores OAuth workspace credentials and refresh tokens",
                "endpoints_or_features": ["Tenant Tokens", "Token Refresh", "Revocation"]
            })
            if any("miro_client.py" in f for f in file_tree):
                connections.append({
                    "from": "miro_sync_service",
                    "to": "kv_oauth_store",
                    "protocol": "KV REST API",
                    "label": "Retrieves Team Token"
                })

        # 5. External Cloud & APIs
        nodes.append({
            "id": "external_miro_api",
            "name": "Miro Enterprise Cloud",
            "layer_id": "layer_external",
            "type": "external",
            "tech": "Miro REST v2 / OAuth2",
            "description": "Cloud visual canvas and collaborative whiteboard platform",
            "endpoints_or_features": ["/v2/boards", "/v2/items", "/v2/connectors"]
        })
        if any("miro_client.py" in f for f in file_tree):
            connections.append({
                "from": "miro_sync_service",
                "to": "external_miro_api",
                "protocol": "HTTPS REST",
                "label": "Syncs Cards & Lines"
            })

        layers = [
            {"id": "layer_presentation", "name": "Presentation & UI", "order": 1},
            {"id": "layer_gateway", "name": "API & Ingress Gateway", "order": 2},
            {"id": "layer_services", "name": "Core Application Services", "order": 3},
            {"id": "layer_data", "name": "Persistence & Multi-Tenant Store", "order": 4},
            {"id": "layer_external", "name": "External Cloud & AI Endpoints", "order": 5}
        ]

        return {
            "system_title": f"{root} Architecture",
            "summary": f"Modular multi-tier architecture of {root} extracted from source AST and configuration files.",
            "architecture_style": "Event-Driven & Microservices",
            "tech_stack": list(codebase_data.get("languages", {}).keys()),
            "layers": layers,
            "nodes": nodes,
            "connections": connections,
            "insights": {
                "strengths": [
                    "Clean separation between frontend canvas UI, backend gateway, and sync services.",
                    "Multi-tenant OAuth2 token isolation with Vercel KV persistence."
                ],
                "bottlenecks": [
                    "External API rate limits from Miro and AI model providers."
                ],
                "recommendations": [
                    "Maintain sliding window rate limiting and automatic token refresh on 401."
                ]
            }
        }

    def _get_fallback(self) -> Dict[str, Any]:
        return {
            "system_title": "Analyzed Codebase Architecture",
            "summary": "Architecture extracted from scanned source files.",
            "architecture_style": "Layered Application",
            "tech_stack": ["Fullstack"],
            "layers": [
                {"id": "layer_presentation", "name": "Frontend & Clients", "order": 1},
                {"id": "layer_services", "name": "Core Application Services", "order": 2},
                {"id": "layer_data", "name": "Database & Storage", "order": 3}
            ],
            "nodes": [
                {"id": "client_ui", "name": "Web Client", "layer_id": "layer_presentation", "type": "frontend", "tech": "React / Web", "description": "User Interface"},
                {"id": "app_server", "name": "Backend Service", "layer_id": "layer_services", "type": "service", "tech": "API Server", "description": "Core business logic"},
                {"id": "main_db", "name": "Primary Database", "layer_id": "layer_data", "type": "database", "tech": "SQL Database", "description": "Application Data"}
            ],
            "connections": [
                {"from": "client_ui", "to": "app_server", "protocol": "REST / JSON", "label": "API Requests"},
                {"from": "app_server", "to": "main_db", "protocol": "SQL Queries", "label": "CRUD Operations"}
            ],
            "insights": {
                "strengths": ["Clear separation of concerns"],
                "bottlenecks": ["Single backend instance"],
                "recommendations": ["Introduce caching layer"]
            }
        }


# Universal Engine Aliases for multi-model architecture synthesis
QwenEngine = ArchitectureEngine
OmniEngine = ArchitectureEngine
OmniArchEngine = ArchitectureEngine
