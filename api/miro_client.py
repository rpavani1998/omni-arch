import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

TYPE_STYLES = {
    "header": {
        "shape": "round_rectangle",
        "fillColor": "#f8fafc",   # Slate 50
        "borderColor": "#cbd5e1", # Slate 300
        "icon": "📌"
    },
    "frontend": {
        "shape": "round_rectangle",
        "fillColor": "#e0f2fe",  # Sky 100
        "borderColor": "#0284c7", # Sky 600
        "icon": "🌐"
    },
    "gateway": {
        "shape": "round_rectangle",
        "fillColor": "#f3e8ff",  # Purple 100
        "borderColor": "#9333ea", # Purple 600
        "icon": "🛡️"
    },
    "service": {
        "shape": "round_rectangle",
        "fillColor": "#ecfdf5",  # Emerald 100
        "borderColor": "#059669", # Emerald 600
        "icon": "⚙️"
    },
    "database": {
        "shape": "round_rectangle",
        "fillColor": "#fef3c7",  # Amber 100
        "borderColor": "#d97706", # Amber 600
        "icon": "🗄️"
    },
    "cache": {
        "shape": "round_rectangle",
        "fillColor": "#ffe4e6",  # Rose 100
        "borderColor": "#e11d48", # Rose 600
        "icon": "⚡"
    },
    "queue": {
        "shape": "round_rectangle",
        "fillColor": "#e0e7ff",  # Indigo 100
        "borderColor": "#4f46e5", # Indigo 600
        "icon": "📬"
    },
    "external": {
        "shape": "round_rectangle",
        "fillColor": "#f1f5f9",  # Slate 100
        "borderColor": "#64748b", # Slate 500
        "icon": "☁️"
    }
}

class MiroClient:
    def __init__(self, access_token: Optional[str] = None, board_id: Optional[str] = None):
        self.access_token = access_token or os.getenv("MIRO_ACCESS_TOKEN", "")
        self.board_id = board_id or os.getenv("MIRO_BOARD_ID", "")
        self.base_url = "https://api.miro.com/v2"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_board_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}/boards/{self.board_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def create_shape(self, content: str, x: float, y: float, shape_type: str = "service", width: float = 300, height: float = 140) -> Dict[str, Any]:
        url = f"{self.base_url}/boards/{self.board_id}/shapes"
        style_cfg = TYPE_STYLES.get(shape_type, TYPE_STYLES["service"])

        payload = {
            "data": {
                "shape": style_cfg["shape"],
                "content": content
            },
            "style": {
                "fillColor": style_cfg["fillColor"],
                "borderColor": style_cfg["borderColor"],
                "borderWidth": "2.0",
                "textAlign": "center",
                "textAlignVertical": "middle"
            },
            "position": {
                "origin": "center",
                "x": x,
                "y": y
            },
            "geometry": {
                "width": width,
                "height": height
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def create_connector(
        self, 
        start_id: str, 
        end_id: str, 
        caption: str = "", 
        stroke_color: str = "#0284c7",
        shape: str = "elbow"
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/boards/{self.board_id}/connectors"
        clean_caption = (caption or "").strip()
        
        payload = {
            "startItem": {
                "id": start_id
            },
            "endItem": {
                "id": end_id
            },
            "shape": shape,
            "style": {
                "strokeColor": stroke_color,
                "strokeWidth": "2.0"
            }
        }
        if clean_caption:
            payload["captions"] = [
                {
                    "content": clean_caption,
                    "position": 0.5
                }
            ]

        try:
            resp = requests.post(url, headers=self.headers, json=payload)
            if resp.status_code in [200, 201]:
                return resp.json()
            else:
                # Fallback to minimal payload while preserving caption
                fallback_payload = {
                    "startItem": {"id": start_id},
                    "endItem": {"id": end_id},
                    "shape": "curved"
                }
                if clean_caption:
                    fallback_payload["captions"] = [
                        {
                            "content": clean_caption
                        }
                    ]
                f_resp = requests.post(url, headers=self.headers, json=fallback_payload)
                if f_resp.status_code in [200, 201]:
                    return f_resp.json()
                print(f"[MiroClient] Connector error ({resp.status_code}): {resp.text}")
                return None
        except Exception as e:
            print(f"[MiroClient] Connector exception: {e}")
            return None

    def create_frame(self, title: str, x: float, y: float, width: float, height: float) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/boards/{self.board_id}/frames"
        payload = {
            "data": {
                "title": title
            },
            "position": {
                "origin": "center",
                "x": x,
                "y": y
            },
            "geometry": {
                "width": width,
                "height": height
            }
        }
        try:
            resp = requests.post(url, headers=self.headers, json=payload)
            if resp.status_code in [200, 201]:
                return resp.json()
            else:
                print(f"[MiroClient] Frame notice ({resp.status_code}): {resp.text}")
                return None
        except Exception as e:
            print(f"[MiroClient] Frame creation exception: {e}")
            return None

    def create_sticky_note(self, content: str, x: float, y: float, color: str = "light_yellow", width: float = 340) -> Dict[str, Any]:
        url = f"{self.base_url}/boards/{self.board_id}/sticky_notes"
        payload = {
            "data": {
                "content": content,
                "shape": "square"
            },
            "style": {
                "fillColor": color,
                "textAlign": "left"
            },
            "position": {
                "origin": "center",
                "x": x,
                "y": y
            },
            "geometry": {
                "width": width
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def sync_architecture_diagram(self, arch_data: Dict[str, Any], start_x: float = -300, start_y: float = -150, perspective: Optional[str] = "overview") -> Dict[str, Any]:
        """Calculates 2D non-overlapping layout with Sugiyama crossing reduction, tier headers, orthogonal elbow connectors, and dedicated perspective Frames."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Multi-perspective offset coordinates to maintain separate gallery frames on the same board
        PERSPECTIVE_OFFSETS = {
            "overview": {"x": 0, "y": 0, "title": "System Architecture (HLD)"},
            "data_flow": {"x": 3600, "y": 0, "title": "Request Lifecycle & API Flow"},
            "database_storage": {"x": 7200, "y": 0, "title": "Data Model & Schema Topology"},
            "devops_pipeline": {"x": 0, "y": 2400, "title": "CI/CD & DevOps Deployment Pipeline"},
            "security_auth": {"x": 3600, "y": 2400, "title": "Security & Zero-Trust Auth"},
            "async_workers": {"x": 7200, "y": 2400, "title": "Async Task Queues & Worker Pipelines"},
            "observability": {"x": 0, "y": 4800, "title": "Observability & SRE Monitoring"},
            "ai_rag": {"x": 3600, "y": 4800, "title": "AI / LLM & RAG Pipeline"},
            # Aliases for compatibility
            "event_driven": {"x": 7200, "y": 2400, "title": "Async Task Queues & Event Pipelines"},
            "devops_cloud": {"x": 0, "y": 2400, "title": "Cloud & Infrastructure"}
        }

        persp_info = PERSPECTIVE_OFFSETS.get(perspective or "overview", {"x": 0, "y": 0, "title": "System Architecture"})
        
        # Apply base offset if provided, or use perspective grid layout
        base_x = start_x + persp_info["x"]
        base_y = start_y + persp_info["y"]

        layers = arch_data.get("layers", [])
        nodes = arch_data.get("nodes", [])
        connections = arch_data.get("connections", [])
        insights = arch_data.get("insights", {})

        # Group nodes by layer
        layer_buckets: Dict[str, List[Dict[str, Any]]] = {}
        layer_id_to_index: Dict[str, int] = {}
        
        for l_idx, layer in enumerate(layers):
            layer_buckets[layer["id"]] = []
            layer_id_to_index[layer["id"]] = l_idx

        for node in nodes:
            lid = node.get("layer_id", "layer_services")
            if lid not in layer_buckets:
                layer_buckets[lid] = []
                layer_id_to_index[lid] = len(layers)
            layer_buckets[lid].append(node)

        # Build bidirectional adjacency for Sugiyama crossing minimization
        adj_map: Dict[str, List[str]] = {}
        for conn in connections:
            src = conn.get("from")
            dst = conn.get("to")
            if src and dst:
                adj_map.setdefault(dst, []).append(src)
                adj_map.setdefault(src, []).append(dst)

        node_pos_index: Dict[str, float] = {}

        # 1. Forward pass: Sort nodes within each tier column to align with connected neighbors
        for l_idx, layer in enumerate(layers):
            lid = layer["id"]
            tier_nodes = layer_buckets.get(lid, [])
            if l_idx > 0 and tier_nodes:
                def get_forward_barycenter(n):
                    neighbors = adj_map.get(n["id"], [])
                    prev_positions = [node_pos_index[nb] for nb in neighbors if nb in node_pos_index]
                    return sum(prev_positions) / len(prev_positions) if prev_positions else 999.0

                tier_nodes.sort(key=get_forward_barycenter)
                layer_buckets[lid] = tier_nodes

            for r_idx, n in enumerate(tier_nodes):
                node_pos_index[n["id"]] = float(r_idx)

        # 2. Backward pass: Refine placement of preceding tiers based on downstream targets
        for l_idx in range(len(layers) - 2, -1, -1):
            lid = layers[l_idx]["id"]
            tier_nodes = layer_buckets.get(lid, [])
            if tier_nodes:
                def get_backward_barycenter(n):
                    neighbors = adj_map.get(n["id"], [])
                    next_positions = [node_pos_index[nb] for nb in neighbors if nb in node_pos_index]
                    return sum(next_positions) / len(next_positions) if next_positions else 999.0

                tier_nodes.sort(key=get_backward_barycenter)
                layer_buckets[lid] = tier_nodes
                for r_idx, n in enumerate(tier_nodes):
                    node_pos_index[n["id"]] = float(r_idx)

        # Generous professional presentation spacing dimensions
        col_width = 660       # 660px tier column width (360px clear corridor between cards for clean lines)
        row_height = 240      # 240px row height (100px clear vertical gap between cards)
        card_width = 300      # 300px card width (ample room for titles & badges)
        card_height = 140     # 140px card height (prevents multi-line text overflow)

        active_layers = [l for l in layers if layer_buckets.get(l["id"])]
        num_cols = max(1, len(active_layers))
        max_rows = max([len(nlist) for nlist in layer_buckets.values()] or [1])

        # Compute dynamic frame dimensions
        frame_w = max(3200, (num_cols * col_width) + 960)
        frame_h = max(1600, (max_rows * row_height) + 650)
        frame_center_x = base_x + ((num_cols - 1) * col_width / 2) - 60
        frame_center_y = base_y

        created_nodes_map: Dict[str, str] = {} # node_id -> miro_item_id
        node_coords_map: Dict[str, Dict[str, Any]] = {} # node_id -> {x, y, col_idx, row_idx}
        all_created_items: List[Dict[str, Any]] = []
        created_frame = None

        # 1. Create Dedicated Perspective Frame on Miro Board
        frame_title = f"{arch_data.get('system_title', 'System')} — {persp_info['title']}"
        try:
            created_frame = self.create_frame(
                title=frame_title,
                x=frame_center_x,
                y=frame_center_y,
                width=frame_w,
                height=frame_h
            )
            if created_frame:
                all_created_items.append(created_frame)
        except Exception as e:
            print(f"[MiroClient] Error creating frame: {e}")

        # 2. Place Architecture Summary Card on left with safe clearance
        summary_content = f"<p><strong style='font-size:16px;color:#0f172a;'>📊 {arch_data.get('system_title', 'System Architecture')}</strong></p><br/>" \
                          f"<p><b>Perspective:</b> {persp_info['title']}</p>" \
                          f"<p><b>Style:</b> {arch_data.get('architecture_style', 'N/A')}</p>" \
                          f"<p><b>Stack:</b> {', '.join(arch_data.get('tech_stack', []))}</p><br/>" \
                          f"<p style='font-size:12px;color:#334155;'><b>Overview:</b> {arch_data.get('summary', '')}</p><br/>" \
                          f"<p style='font-size:12px;color:#1e293b;'><b>Key Strengths:</b><br/>• " + "<br/>• ".join(insights.get("strengths", ["Modular microservice design", "Decoupled data boundaries"])[:2]) + "</p>"

        try:
            summary_sticky = self.create_sticky_note(
                content=summary_content, 
                x=base_x - 500, 
                y=base_y, 
                color="light_yellow", 
                width=340
            )
            all_created_items.append(summary_sticky)
        except Exception as e:
            print(f"[MiroClient] Error creating summary sticky: {e}")

        # 3. Create Tier Column Headers and Node Shapes
        shapes_to_create = []
        header_y = base_y - ((max_rows - 1) * row_height / 2) - 150
        col_idx = 0

        for layer in layers:
            lid = layer["id"]
            layer_nodes = layer_buckets.get(lid, [])
            if not layer_nodes:
                continue

            current_x = base_x + (col_idx * col_width)
            total_in_col = len(layer_nodes)

            # Add Tier Column Header Shape
            layer_title = layer.get("name", f"Tier {col_idx + 1}")
            shapes_to_create.append({
                "node_id": f"__header_{lid}",
                "content": f"<p><strong style='font-size:12px;color:#334155;'>TIER {col_idx + 1}: {layer_title.upper()}</strong></p>",
                "x": current_x,
                "y": header_y,
                "shape_type": "header",
                "width": card_width,
                "height": 42,
                "is_header": True
            })
            
            for row_idx, node in enumerate(layer_nodes):
                current_y = base_y + (row_idx * row_height) - ((total_in_col - 1) * row_height / 2)
                node_type = node.get("type", "service")
                style_cfg = TYPE_STYLES.get(node_type, TYPE_STYLES["service"])
                icon = style_cfg.get("icon", "⚙️")
                
                tech_str = node.get('tech', '')
                desc_str = node.get('description', '')
                
                html_content = f"<p><strong style='font-size:13px;color:#0f172a;'>{icon} {node['name']}</strong></p>"
                if tech_str:
                    html_content += f"<p><em style='font-size:11px;color:#475569;'>{tech_str}</em></p>"
                if desc_str:
                    clean_desc = desc_str if len(desc_str) <= 75 else desc_str[:72] + "..."
                    html_content += f"<p style='font-size:11px;color:#334155;'>{clean_desc}</p>"

                node_coords_map[node["id"]] = {
                    "x": current_x,
                    "y": current_y,
                    "col_idx": col_idx,
                    "row_idx": row_idx
                }

                shapes_to_create.append({
                    "node_id": node["id"],
                    "content": html_content,
                    "x": current_x,
                    "y": current_y,
                    "shape_type": node_type,
                    "width": card_width,
                    "height": card_height,
                    "is_header": False
                })
            col_idx += 1

        # Execute shape creations in parallel (up to 8 concurrent threads)
        def create_single_shape(task):
            try:
                resp = self.create_shape(
                    content=task["content"],
                    x=task["x"],
                    y=task["y"],
                    shape_type=task["shape_type"],
                    width=task.get("width", card_width),
                    height=task.get("height", card_height)
                )
                return task["node_id"], resp, task.get("is_header", False)
            except Exception as e:
                print(f"[MiroClient] Error creating shape {task['node_id']}: {e}")
                return task["node_id"], None, task.get("is_header", False)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(create_single_shape, t) for t in shapes_to_create]
            for future in as_completed(futures):
                node_id, resp, is_header = future.result()
                if resp:
                    if not is_header:
                        created_nodes_map[node_id] = resp["id"]
                    all_created_items.append(resp)

        # 4. Draw Connectors with Smart Routing & Concise Captions
        connectors_to_create = []
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            if from_id in created_nodes_map and to_id in created_nodes_map:
                start_miro_id = created_nodes_map[from_id]
                end_miro_id = created_nodes_map[to_id]
                
                protocol = (conn.get("protocol") or "").strip()
                label = (conn.get("label") or "").strip()
                
                # Filter redundant language/internal prefixes
                clean_proto = protocol
                for generic in ["Python API", "In-Memory", "Internal API", "Method Call", "Local Call"]:
                    if clean_proto.lower() == generic.lower():
                        clean_proto = ""
                        break

                if label and not clean_proto:
                    caption = label
                elif clean_proto and not label:
                    caption = clean_proto
                elif clean_proto and label:
                    caption = clean_proto if len(clean_proto) <= 16 else label
                else:
                    caption = ""

                if len(caption) > 20:
                    caption = caption[:18] + ".."

                src_coord = node_coords_map.get(from_id, {"col_idx": 0, "row_idx": 0, "x": 0, "y": 0})
                dst_coord = node_coords_map.get(to_id, {"col_idx": 0, "row_idx": 0, "x": 0, "y": 0})

                conn_shape = "elbow" if src_coord["col_idx"] != dst_coord["col_idx"] else "curved"

                # Smart edge colors by protocol
                proto_lower = protocol.lower() + " " + label.lower()
                stroke_color = "#0284c7" # default sky blue
                if any(k in proto_lower for k in ["kafka", "queue", "event", "pubsub", "async"]):
                    stroke_color = "#7c3aed" # Purple for async events
                elif any(k in proto_lower for k in ["sql", "db", "postgres", "query", "redis", "cache"]):
                    stroke_color = "#d97706" # Amber for database / cache
                elif any(k in proto_lower for k in ["auth", "jwt", "oauth", "security", "token"]):
                    stroke_color = "#dc2626" # Red for auth boundaries
                elif any(k in proto_lower for k in ["grpc", "rpc", "internal"]):
                    stroke_color = "#059669" # Emerald for internal gRPC
                elif any(k in proto_lower for k in ["llm", "ai", "qwen", "inference", "prompt"]):
                    stroke_color = "#6366f1" # Indigo for AI/LLM pipelines

                connectors_to_create.append({
                    "start_id": start_miro_id,
                    "end_id": end_miro_id,
                    "caption": caption,
                    "shape": conn_shape,
                    "stroke_color": stroke_color
                })

        def create_single_conn(task):
            try:
                return self.create_connector(
                    start_id=task["start_id"],
                    end_id=task["end_id"],
                    caption=task["caption"],
                    stroke_color=task["stroke_color"],
                    shape=task["shape"]
                )
            except Exception as e:
                print(f"[MiroClient] Error creating connector: {e}")
                return None

        created_connectors = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            conn_futures = [executor.submit(create_single_conn, t) for t in connectors_to_create]
            for future in as_completed(conn_futures):
                c_resp = future.result()
                if c_resp:
                    created_connectors.append(c_resp)

        frame_widget_id = created_frame.get("id") if created_frame else None
        board_view_url = f"https://miro.com/app/board/{self.board_id}/"
        if frame_widget_id:
            board_view_url += f"?moveToWidget={frame_widget_id}"

        return {
            "board_id": self.board_id,
            "board_url": board_view_url,
            "frame_id": frame_widget_id,
            "frame_title": frame_title,
            "created_nodes": len(created_nodes_map),
            "created_connectors": len(created_connectors),
            "total_items": len(all_created_items) + len(created_connectors)
        }
