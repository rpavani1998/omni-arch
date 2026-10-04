import os
import requests
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

TYPE_STYLES = {
    "header": {
        "shape": "round_rectangle",
        "fillColor": "#f8fafc",   # Slate 50
        "borderColor": "#cbd5e1", # Slate 300
    },
    "frontend": {
        "shape": "round_rectangle",
        "fillColor": "#e0f2fe",  # Sky 100
        "borderColor": "#0284c7", # Sky 600
    },
    "gateway": {
        "shape": "round_rectangle",
        "fillColor": "#f3e8ff",  # Purple 100
        "borderColor": "#9333ea", # Purple 600
    },
    "service": {
        "shape": "round_rectangle",
        "fillColor": "#ecfdf5",  # Emerald 100
        "borderColor": "#059669", # Emerald 600
    },
    "database": {
        "shape": "round_rectangle",
        "fillColor": "#fef3c7",  # Amber 100
        "borderColor": "#d97706", # Amber 600
    },
    "cache": {
        "shape": "round_rectangle",
        "fillColor": "#ffe4e6",  # Rose 100
        "borderColor": "#e11d48", # Rose 600
    },
    "queue": {
        "shape": "round_rectangle",
        "fillColor": "#e0e7ff",  # Indigo 100
        "borderColor": "#4f46e5", # Indigo 600
    },
    "external": {
        "shape": "round_rectangle",
        "fillColor": "#f1f5f9",  # Slate 100
        "borderColor": "#64748b", # Slate 500
    }
}

class MiroClient:
    def __init__(self, access_token: Optional[str] = None, board_id: Optional[str] = None, team_id: Optional[str] = None):
        self.team_id = team_id
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

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Executes HTTP request with automatic token refresh on 401 Unauthorized."""
        headers = kwargs.pop("headers", None) or self.headers
        fn = getattr(requests, method.lower(), None)
        if fn is not None:
            resp = fn(url, headers=headers, **kwargs)
        else:
            resp = requests.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401 and self.team_id:
            try:
                try:
                    from backend.oauth import oauth_manager
                except ImportError:
                    from oauth import oauth_manager
                new_token = oauth_manager.refresh_access_token(self.team_id)
                if new_token:
                    self.access_token = new_token
                    retry_headers = self.headers
                    if fn is not None:
                        resp = fn(url, headers=retry_headers, **kwargs)
                    else:
                        resp = requests.request(method, url, headers=retry_headers, **kwargs)
            except Exception as e:
                print(f"[MiroClient] Token refresh failed: {e}")
        return resp


    def get_board_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}/boards/{self.board_id}"
        resp = self._request("GET", url)
        resp.raise_for_status()
        return resp.json()

    def get_board_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves existing board items for in-place incremental diffing."""
        url = f"{self.base_url}/boards/{self.board_id}/items?limit={limit}"
        try:
            resp = self._request("GET", url)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception as e:
            print(f"[MiroClient] Error fetching board items: {e}")
        return []

    def get_board_connectors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves existing board connectors."""
        url = f"{self.base_url}/boards/{self.board_id}/connectors?limit={limit}"
        try:
            resp = self._request("GET", url)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception as e:
            print(f"[MiroClient] Error fetching board connectors: {e}")
        return []

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
        resp = self._request("POST", url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_shape(
        self, 
        shape_id: str, 
        content: Optional[str] = None, 
        x: Optional[float] = None, 
        y: Optional[float] = None, 
        shape_type: str = "service",
        width: float = 300, 
        height: float = 140
    ) -> Optional[Dict[str, Any]]:
        """Updates an existing shape in-place without deleting or re-creating it."""
        url = f"{self.base_url}/boards/{self.board_id}/shapes/{shape_id}"
        style_cfg = TYPE_STYLES.get(shape_type, TYPE_STYLES["service"])

        payload: Dict[str, Any] = {
            "style": {
                "fillColor": style_cfg["fillColor"],
                "borderColor": style_cfg["borderColor"],
                "borderWidth": "2.0",
                "textAlign": "center",
                "textAlignVertical": "middle"
            },
            "geometry": {
                "width": width,
                "height": height
            }
        }
        if content is not None:
            payload["data"] = {
                "content": content,
                "shape": style_cfg["shape"]
            }
        if x is not None and y is not None:
            payload["position"] = {
                "origin": "center",
                "x": x,
                "y": y
            }

        try:
            resp = self._request("PATCH", url, json=payload)
            if resp.status_code in [200, 201]:
                return resp.json()
            print(f"[MiroClient] Update shape error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[MiroClient] Update shape exception for {shape_id}: {e}")
        return None

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
            resp = self._request("POST", url, json=payload)
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
                f_resp = self._request("POST", url, json=fallback_payload)
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
            resp = self._request("POST", url, json=payload)
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
        resp = self._request("POST", url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_sticky_note(self, note_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Updates an existing sticky note in-place."""
        url = f"{self.base_url}/boards/{self.board_id}/sticky_notes/{note_id}"
        payload = {
            "data": {
                "content": content
            }
        }
        try:
            resp = self._request("PATCH", url, json=payload)
            if resp.status_code in [200, 201]:
                return resp.json()
        except Exception as e:
            print(f"[MiroClient] Error updating sticky note {note_id}: {e}")
        return None

    def delete_item(self, item_id: str) -> bool:
        """Deletes an item from the board."""
        url = f"{self.base_url}/boards/{self.board_id}/items/{item_id}"
        try:
            resp = self._request("DELETE", url)
            return resp.status_code in [200, 204]
        except Exception as e:
            print(f"[MiroClient] Error deleting item {item_id}: {e}")
            return False

    def delete_connector(self, connector_id: str) -> bool:
        """Deletes a connector from the board."""
        url = f"{self.base_url}/boards/{self.board_id}/connectors/{connector_id}"
        try:
            resp = self._request("DELETE", url)
            return resp.status_code in [200, 204]
        except Exception as e:
            print(f"[MiroClient] Error deleting connector {connector_id}: {e}")
            return False


    def sync_architecture_diagram(self, arch_data: Dict[str, Any], start_x: float = -300, start_y: float = -150, perspective: Optional[str] = "overview") -> Dict[str, Any]:
        """
        Calculates 2D non-overlapping layout with Sugiyama crossing reduction, tier headers, and dedicated perspective Frames.
        Performs in-place incremental diffing on PR updates so existing shapes are updated without canvas recreation or clutter.
        """
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
                layer_id_to_index[lid] = len(layer_buckets)
            layer_buckets[lid].append(node)

        # Fallback / augment layers if not fully specified in arch_data
        if not layers:
            DEFAULT_TIER_NAMES = {
                "layer_presentation": "Presentation Tier",
                "layer_gateway": "Ingress & Gateway",
                "layer_services": "Core Services",
                "layer_data": "Data & Persistence",
                "layer_external": "External Integrations"
            }
            layers = [
                {"id": lid, "name": DEFAULT_TIER_NAMES.get(lid, lid.replace("layer_", "").replace("_", " ").title())}
                for lid in layer_buckets.keys()
            ]
        else:
            existing_lids = {l["id"] for l in layers}
            for lid in layer_buckets.keys():
                if lid not in existing_lids:
                    layers.append({"id": lid, "name": lid.replace("layer_", "").replace("_", " ").title()})

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

        # Bounding box of current perspective
        min_bound_x = base_x - 850
        max_bound_x = base_x + frame_w + 400
        min_bound_y = base_y - (frame_h / 2) - 400
        max_bound_y = base_y + (frame_h / 2) + 400

        # Fetch existing board items for in-place diffing
        existing_items = self.get_board_items(limit=100)
        
        # Categorize items residing in this perspective frame
        existing_shapes_by_name: Dict[str, Dict[str, Any]] = {}
        existing_header_shapes: Dict[str, Dict[str, Any]] = {}
        existing_sticky_note: Optional[Dict[str, Any]] = None
        existing_frame: Optional[Dict[str, Any]] = None

        def extract_name_from_content(html_str: str) -> str:
            # Extract plain text from <strong>...</strong> or first line
            match = re.search(r"<strong>(.*?)</strong>", html_str or "", re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()
            clean = re.sub(r"<[^>]+>", "", html_str or "").strip()
            return clean.split("\n")[0].strip().lower()

        for item in existing_items:
            pos = item.get("position", {})
            ix = pos.get("x", 0)
            iy = pos.get("y", 0)
            
            # Check if item is inside this perspective region
            if min_bound_x <= ix <= max_bound_x and min_bound_y <= iy <= max_bound_y:
                item_type = item.get("type", "")
                data = item.get("data", {})
                content = data.get("content", "")
                
                if item_type == "shape":
                    if "TIER" in content.upper() and "•" in content:
                        header_key = re.sub(r"<[^>]+>", "", content).strip().lower()
                        existing_header_shapes[header_key] = item
                    else:
                        name_key = extract_name_from_content(content)
                        if name_key:
                            existing_shapes_by_name[name_key] = item
                elif item_type == "sticky_note":
                    existing_sticky_note = item
                elif item_type == "frame":
                    if persp_info["title"].lower() in data.get("title", "").lower():
                        existing_frame = item

        created_nodes_map: Dict[str, str] = {} # node_id -> miro_item_id
        node_coords_map: Dict[str, Dict[str, Any]] = {} # node_id -> {x, y, col_idx, row_idx}
        all_created_items: List[Dict[str, Any]] = []
        
        updated_nodes_count = 0
        created_nodes_count = 0
        deleted_nodes_count = 0

        # 1. Perspective Frame on Miro Board
        frame_title = f"{arch_data.get('system_title', 'System')} — {persp_info['title']}"
        target_frame = existing_frame
        if not target_frame:
            try:
                target_frame = self.create_frame(
                    title=frame_title,
                    x=frame_center_x,
                    y=frame_center_y,
                    width=frame_w,
                    height=frame_h
                )
            except Exception as e:
                print(f"[MiroClient] Error creating frame: {e}")
        if target_frame:
            all_created_items.append(target_frame)

        # 2. Place / In-Place Update Architecture Summary Card on left
        summary_content = f"<p><strong>{arch_data.get('system_title', 'System Architecture')}</strong></p><br/>" \
                          f"<p><b>Perspective:</b> {persp_info['title']}</p>" \
                          f"<p><b>Style:</b> {arch_data.get('architecture_style', 'N/A')}</p>" \
                          f"<p><b>Stack:</b> {', '.join(arch_data.get('tech_stack', []))}</p><br/>" \
                          f"<p><b>Overview:</b> {arch_data.get('summary', '')}</p><br/>" \
                          f"<p><b>Key Strengths:</b><br/>• " + "<br/>• ".join(insights.get("strengths", ["Modular microservice design", "Decoupled data boundaries"])[:2]) + "</p>"

        if existing_sticky_note:
            try:
                updated_sticky = self.update_sticky_note(existing_sticky_note["id"], summary_content)
                all_created_items.append(updated_sticky or existing_sticky_note)
            except Exception as e:
                print(f"[MiroClient] Error updating summary sticky: {e}")
        else:
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

        # 3. Create / In-Place Update Tier Column Headers and Node Shapes
        header_y = base_y - ((max_rows - 1) * row_height / 2) - 150
        col_idx = 0
        matched_shape_ids = set()

        tasks_to_execute = []

        for layer in layers:
            lid = layer["id"]
            layer_nodes = layer_buckets.get(lid, [])
            if not layer_nodes:
                continue

            current_x = base_x + (col_idx * col_width)
            total_in_col = len(layer_nodes)

            # Tier Column Header Shape
            layer_title = layer.get("name", f"Tier {col_idx + 1}")
            header_content = f"<p><strong>TIER {col_idx + 1} • {layer_title.upper()}</strong></p>"
            header_key = f"tier {col_idx + 1} • {layer_title.upper()}".lower()

            existing_hdr = existing_header_shapes.get(header_key)
            tasks_to_execute.append({
                "action": "update" if existing_hdr else "create",
                "item_id": existing_hdr.get("id") if existing_hdr else None,
                "node_id": f"__header_{lid}",
                "content": header_content,
                "x": current_x,
                "y": header_y,
                "shape_type": "header",
                "width": card_width,
                "height": 42,
                "is_header": True
            })
            if existing_hdr:
                matched_shape_ids.add(existing_hdr["id"])
            
            for row_idx, node in enumerate(layer_nodes):
                current_y = base_y + (row_idx * row_height) - ((total_in_col - 1) * row_height / 2)
                node_type = node.get("type", "service")
                
                tech_str = node.get('tech', '')
                desc_str = node.get('description', '')
                
                html_content = f"<p><strong>{node['name']}</strong></p>"
                if tech_str:
                    html_content += f"<p><em>{tech_str}</em></p>"
                if desc_str:
                    clean_desc = desc_str if len(desc_str) <= 75 else desc_str[:72] + "..."
                    html_content += f"<p>{clean_desc}</p>"

                node_coords_map[node["id"]] = {
                    "x": current_x,
                    "y": current_y,
                    "col_idx": col_idx,
                    "row_idx": row_idx
                }

                # Match by component name
                name_key = node["name"].strip().lower()
                existing_shape = existing_shapes_by_name.get(name_key)

                if existing_shape:
                    matched_shape_ids.add(existing_shape["id"])
                    tasks_to_execute.append({
                        "action": "update",
                        "item_id": existing_shape["id"],
                        "node_id": node["id"],
                        "content": html_content,
                        "x": current_x,
                        "y": current_y,
                        "shape_type": node_type,
                        "width": card_width,
                        "height": card_height,
                        "is_header": False
                    })
                else:
                    tasks_to_execute.append({
                        "action": "create",
                        "item_id": None,
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

        # In-place clean up obsolete shapes removed in this PR
        for name_key, old_shape in existing_shapes_by_name.items():
            if old_shape["id"] not in matched_shape_ids:
                try:
                    self.delete_item(old_shape["id"])
                    deleted_nodes_count += 1
                except Exception as e:
                    print(f"[MiroClient] Error pruning obsolete shape {old_shape['id']}: {e}")

        # Execute shape operations in parallel
        def process_single_shape_task(task):
            try:
                if task["action"] == "update" and task["item_id"]:
                    resp = self.update_shape(
                        shape_id=task["item_id"],
                        content=task["content"],
                        x=task["x"],
                        y=task["y"],
                        shape_type=task["shape_type"],
                        width=task.get("width", card_width),
                        height=task.get("height", card_height)
                    )
                    return task["node_id"], resp or {"id": task["item_id"]}, task.get("is_header", False), "updated"
                else:
                    resp = self.create_shape(
                        content=task["content"],
                        x=task["x"],
                        y=task["y"],
                        shape_type=task["shape_type"],
                        width=task.get("width", card_width),
                        height=task.get("height", card_height)
                    )
                    return task["node_id"], resp, task.get("is_header", False), "created"
            except Exception as e:
                print(f"[MiroClient] Error processing shape {task['node_id']}: {e}")
                return task["node_id"], None, task.get("is_header", False), "error"

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_single_shape_task, t) for t in tasks_to_execute]
            for future in as_completed(futures):
                node_id, resp, is_header, op_type = future.result()
                if resp:
                    if not is_header:
                        created_nodes_map[node_id] = resp["id"]
                        if op_type == "updated":
                            updated_nodes_count += 1
                        elif op_type == "created":
                            created_nodes_count += 1
                    all_created_items.append(resp)

        # 4. Clean up old connectors in frame and wire updated connectors
        existing_conns = self.get_board_connectors(limit=100)
        valid_miro_ids = set(created_nodes_map.values())
        
        for c in existing_conns:
            start_item = c.get("startItem", {}).get("id")
            end_item = c.get("endItem", {}).get("id")
            if start_item in valid_miro_ids or end_item in valid_miro_ids:
                try:
                    self.delete_connector(c["id"])
                except Exception as e:
                    print(f"[MiroClient] Error clearing old connector {c['id']}: {e}")

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

        frame_widget_id = target_frame.get("id") if target_frame else None
        board_view_url = f"https://miro.com/app/board/{self.board_id}/"
        if frame_widget_id:
            board_view_url += f"?moveToWidget={frame_widget_id}"

        return {
            "board_id": self.board_id,
            "board_url": board_view_url,
            "frame_id": frame_widget_id,
            "frame_title": frame_title,
            "perspective": perspective,
            "updated_nodes": updated_nodes_count,
            "created_nodes": created_nodes_count,
            "deleted_nodes": deleted_nodes_count,
            "created_connectors": len(created_connectors),
            "total_items": len(all_created_items) + len(created_connectors),
            "sync_mode": "incremental_update" if updated_nodes_count > 0 else "initial_creation"
        }
