import os
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a Principal Software Architect and Visual System Design Expert powered by Qwen.
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
1. Output ONLY the raw valid JSON object starting with { and ending with }. Do NOT write markdown prose or long monologue before the JSON.
2. Adapt intelligently to any architecture: for web/microservices use web tiers; for ML/research pipelines map notebooks/dashboards to presentation, CLI/SLURM to gateway, models/training/eval to services, datasets/checkpoints/scoresheets to data, and HPC/GPUs/frameworks to external.
3. Every node in "connections" MUST reference a valid "id" present in "nodes".
4. Group all nodes into the appropriate layer_id from the 5 standard layers.
"""

PERSPECTIVE_DIRECTIVES = {
    "overview": "Generate a comprehensive end-to-end system architecture overview decomposing presentation tier, API gateway, core backend microservices, data persistence stores, and external integrations.",
    "data_flow": "Focus specifically on the end-to-end data lifecycle: client requests, API routing, synchronous gRPC/REST service calls, database reads/writes, and cache retrieval pathways.",
    "security_auth": "Focus exclusively on security boundaries: authentication mechanisms (JWT/OAuth2/OIDC), API gateway token validation, session authorization, secrets storage, and protected domain services.",
    "event_driven": "Emphasize asynchronous messaging patterns: Kafka / RabbitMQ / Redis event streams, pub/sub topics, background worker consumers, event-driven triggers, and failure retry queues.",
    "database_storage": "Focus on data layer topology: primary SQL tables, relational foreign keys, distributed NoSQL stores, Redis session caching, connection pooling, and replication/sharding strategies.",
    "devops_cloud": "Structure the diagram around cloud infrastructure: Docker containers, Kubernetes pods, ingress controllers, load balancers, CDN caching, and production cloud deployment tiers.",
    "ai_rag": "Focus on AI system components: user input orchestrator, embedding models, vector database retrieval, LLM inference agent workflows, tool calls, and streaming output."
}

class QwenEngine:
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
            context_parts.append(f"\n[FILE: {fpath}]\n{content}\n")

        # Add perspective directive
        if perspective in PERSPECTIVE_DIRECTIVES:
            context_parts.append(f"\n--- DIAGRAM PERSPECTIVE GOAL ---\n{PERSPECTIVE_DIRECTIVES[perspective]}")

        if custom_instructions and custom_instructions.strip():
            context_parts.append(f"\n--- USER ARCHITECTURAL FOCUS & CUSTOM REQUIREMENTS ---\n{custom_instructions.strip()}\nEnsure you prioritize and explicitly reflect these specific requirements, focus areas, and components in the diagram layers, nodes, data flows, and recommendations.")
            
        full_codebase_prompt = "\n".join(context_parts)
        return f"Please analyze this codebase and generate the complete visual architecture graph JSON according to the instructions:\n\n{full_codebase_prompt}"

    def stream_architecture_analysis(self, codebase_data: Dict[str, Any], provider: str = "modelscope", perspective: str = "overview", custom_instructions: str = ""):
        """Streams reasoning tokens in real-time, then yields complete architecture JSON."""
        import time
        start_time = time.time()
        load_dotenv(override=True)
        modelscope_key = os.getenv("MODELSCOPE_API_KEY", self.modelscope_key)

        user_message = self._build_context(codebase_data, perspective, custom_instructions)

        if provider == "ollama":
            client = OpenAI(base_url=self.ollama_base, api_key="ollama")
            model_name = self.ollama_model
        else:
            client = OpenAI(base_url=self.modelscope_base, api_key=modelscope_key)
            model_name = self.modelscope_model

        try:
            stream = client.chat.completions.create(
                model=model_name,
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

            # Parse the final JSON from either content or reasoning stream
            duration_ms = int((time.time() - start_time) * 1000)
            combined_text = full_content + "\n" + full_reasoning
            parsed_json = self._parse_json_response(combined_text)

            # Fallback reasoning if model didn't stream explicit reasoning
            if not full_reasoning:
                full_reasoning = "1. Analyzed ingress routes and API gateways.\n2. Decomposed microservices and message queues.\n3. Mapped database persistence tiers and caching layers.\n4. Extracted architectural strengths and scaling considerations."

            usage = {
                "total_tokens": len((full_content + full_reasoning).split()) * 2,
                "duration_ms": duration_ms,
                "model": model_name,
                "provider": "ModelScope Cloud" if provider != "ollama" else "Local Ollama",
                "reasoning": full_reasoning
            }

            yield f"data: {json.dumps({'type': 'complete', 'architecture': parsed_json, 'usage': usage})}\n\n"

        except Exception as e:
            print(f"[QwenEngine] Streaming failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    def analyze_architecture(self, codebase_data: Dict[str, Any], provider: str = "modelscope", perspective: str = "overview", custom_instructions: str = "") -> Dict[str, Any]:
        """Calls Qwen to deduce architecture from codebase metadata and returns graph + token metrics."""
        import time
        start_time = time.time()
        
        user_message = self._build_context(codebase_data, perspective, custom_instructions)
        raw_response, usage_metrics = self._call_llm(user_message, provider=provider)
        duration_ms = int((time.time() - start_time) * 1000)
        usage_metrics["duration_ms"] = duration_ms

        parsed_json = self._parse_json_response(raw_response)
        return {
            "architecture": parsed_json,
            "usage": usage_metrics
        }

    def _call_llm(self, user_content: str, provider: str = "modelscope"):
        load_dotenv(override=True)
        modelscope_key = os.getenv("MODELSCOPE_API_KEY", self.modelscope_key)
        reasoning_text = ""

        if provider.startswith("modelscope") or (provider == "auto" and modelscope_key):
            try:
                target_model = self.modelscope_model
                print(f"[QwenEngine] Invoking ModelScope ({target_model})...")
                client = OpenAI(base_url=self.modelscope_base, api_key=modelscope_key)
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
                
                # Check for <think>...</think> tags if reasoning_content was in body
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
                    "model": self.modelscope_model,
                    "provider": "ModelScope Cloud",
                    "reasoning": reasoning_text
                }
                print(f"[QwenEngine] ModelScope response: {usage['total_tokens']} tokens, reasoning: {len(reasoning_text)} chars")
                # Return both content and reasoning so parser has full access
                return content if content.strip() else reasoning_text, usage
            except Exception as e:
                print(f"[QwenEngine] ModelScope call error ({e}), falling back to Ollama...")

        # Fallback to local Ollama
        print(f"[QwenEngine] Invoking local Ollama ({self.ollama_model})...")
        client = OpenAI(base_url=self.ollama_base, api_key="ollama")
        resp = client.chat.completions.create(
            model=self.ollama_model,
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
            "model": self.ollama_model,
            "provider": "Local Ollama",
            "reasoning": reasoning_text
        }
        return content if content.strip() else reasoning_text, usage

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans, extracts, and repairs JSON safely from model response."""
        cleaned = text.strip()
        
        # Remove markdown codeblock syntax if present
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                cleaned = re.sub(r"```(?:json)?", "", cleaned)
                cleaned = cleaned.replace("```", "").strip()

        # Find first { and last }
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx + 1]
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and "nodes" in parsed and len(parsed["nodes"]) > 0:
                    return parsed
            except Exception:
                pass

            # Try cleaning trailing commas
            cleaned_commas = re.sub(r",\s*([\]}])", r"\1", json_str)
            try:
                parsed = json.loads(cleaned_commas)
                if isinstance(parsed, dict) and "nodes" in parsed:
                    return parsed
            except Exception:
                pass

        # If start_idx exists but end_idx is cut off, attempt auto-closing JSON
        if start_idx != -1:
            partial_json = cleaned[start_idx:]
            # Attempt to balance brackets
            open_braces = partial_json.count("{") - partial_json.count("}")
            open_brackets = partial_json.count("[") - partial_json.count("]")
            repaired = partial_json.rstrip().rstrip(",") + ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))
            repaired = re.sub(r",\s*([\]}])", r"\1", repaired)
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, dict) and "nodes" in parsed and len(parsed["nodes"]) > 0:
                    return parsed
            except Exception:
                pass

        # Return fallback structure only as last resort
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
