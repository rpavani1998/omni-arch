import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

TYPE_STYLES = {
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
        "shape": "can",
        "fillColor": "#fef3c7",  # Amber 100
        "borderColor": "#d97706", # Amber 600
        "icon": "🗄️"
    },
    "cache": {
        "shape": "can",
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
        "shape": "cloud",
        "fillColor": "#f1f5f9",  # Slate 100
        "borderColor": "#475569", # Slate 600
        "icon": "🔌"
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

    def create_shape(self, content: str, x: float, y: float, shape_type: str = "service", width: float = 220, height: float = 110) -> Dict[str, Any]:
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

    def create_connector(self, start_id: str, end_id: str, caption: str = "", stroke_color: str = "#0284c7") -> Dict[str, Any]:
        url = f"{self.base_url}/boards/{self.board_id}/connectors"
        payload = {
            "startItem": {"id": start_id},
            "endItem": {"id": end_id},
            "shape": "curved",
            "style": {
                "strokeColor": stroke_color,
                "strokeWidth": "2.0",
                "endStrokeCap": "stealth"
            }
        }
        if caption:
            payload["captions"] = [{"content": caption}]

        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def create_sticky_note(self, content: str, x: float, y: float, color: str = "light_yellow", width: float = 280) -> Dict[str, Any]:
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

    def create_frame(self, title: str, x: float, y: float, width: float, height: float) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/boards/{self.board_id}/frames"
        payload = {
            "data": {
                "title": title
            },
            "style": {
                "fillColor": "#ffffff"
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

    def sync_architecture_diagram(self, arch_data: Dict[str, Any], start_x: float = -300, start_y: float = -150, perspective: Optional[str] = "overview") -> Dict[str, Any]:
        """Calculates 2D non-overlapping layout, creates a dedicated perspective Frame, and renders the full architecture graph onto Miro."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Multi-perspective offset coordinates to maintain separate gallery frames on the same board
        PERSPECTIVE_OFFSETS = {
            "overview": {"x": 0, "y": 0, "title": "System Overview"},
            "data_flow": {"x": 2800, "y": 0, "title": "Data Flow & Request Lifecycle"},
            "security_auth": {"x": 5600, "y": 0, "title": "Security & Zero-Trust Auth"},
            "event_driven": {"x": 0, "y": 1800, "title": "Event-Driven & Async Pipelines"},
            "database_storage": {"x": 2800, "y": 1800, "title": "Database & Storage Topology"},
            "devops_cloud": {"x": 5600, "y": 1800, "title": "Cloud & Infrastructure"},
            "ai_rag": {"x": 0, "y": 3600, "title": "AI / LLM & RAG Pipeline"}
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
        for layer in layers:
            layer_buckets[layer["id"]] = []

        for node in nodes:
            lid = node.get("layer_id", "layer_services")
            if lid not in layer_buckets:
                layer_buckets[lid] = []
            layer_buckets[lid].append(node)

        # Generous collision-free spacing dimensions
        col_width = 440       # 440px tier column width (200px clear corridor between cards)
        row_height = 200      # 200px row height (90px clear vertical gap)
        card_width = 240
        card_height = 110

        active_layers = [l for l in layers if layer_buckets.get(l["id"])]
        num_cols = max(1, len(active_layers))
        max_rows = max([len(nlist) for nlist in layer_buckets.values()] or [1])

        # Compute dynamic frame dimensions
        frame_w = max(2200, (num_cols * col_width) + 700)
        frame_h = max(1200, (max_rows * row_height) + 400)
        frame_center_x = base_x + ((num_cols - 1) * col_width / 2) - 100
        frame_center_y = base_y

        created_nodes_map: Dict[str, str] = {} # node_id -> miro_item_id
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

        # 2. Place Architecture Summary Card on left
        summary_content = f"<b>{arch_data.get('system_title', 'System Architecture')}</b><br/><br/>" \
                          f"<b>Perspective:</b> {persp_info['title']}<br/>" \
                          f"<b>Style:</b> {arch_data.get('architecture_style', 'N/A')}<br/>" \
                          f"<b>Stack:</b> {', '.join(arch_data.get('tech_stack', []))}<br/><br/>" \
                          f"<b>Overview:</b> {arch_data.get('summary', '')}<br/><br/>" \
                          f"<b>Key Insights:</b><br/>• " + "<br/>• ".join(insights.get("strengths", ["Modular design"])[:2])

        try:
            summary_sticky = self.create_sticky_note(
                content=summary_content, 
                x=base_x - 420, 
                y=base_y, 
                color="light_yellow", 
                width=300
            )
            all_created_items.append(summary_sticky)
        except Exception as e:
            print(f"[MiroClient] Error creating summary sticky: {e}")

        # 3. Prepare all node shape tasks
        shapes_to_create = []
        col_idx = 0
        for layer in layers:
            lid = layer["id"]
            layer_nodes = layer_buckets.get(lid, [])
            if not layer_nodes:
                continue

            current_x = base_x + (col_idx * col_width)
            total_in_col = len(layer_nodes)
            
            for row_idx, node in enumerate(layer_nodes):
                current_y = base_y + (row_idx * row_height) - ((total_in_col - 1) * row_height / 2)
                node_type = node.get("type", "service")
                
                html_content = f"<strong>{node['name']}</strong><br/>" \
                               f"<small style='color:#475569;'>{node.get('tech', '')}</small><br/>" \
                               f"<span style='font-size:11px;'>{node.get('description', '')}</span>"

                shapes_to_create.append({
                    "node_id": node["id"],
                    "content": html_content,
                    "x": current_x,
                    "y": current_y,
                    "shape_type": node_type
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
                    width=card_width,
                    height=card_height
                )
                return task["node_id"], resp
            except Exception as e:
                print(f"[MiroClient] Error creating shape {task['node_id']}: {e}")
                return task["node_id"], None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(create_single_shape, t) for t in shapes_to_create]
            for future in as_completed(futures):
                node_id, resp = future.result()
                if resp:
                    created_nodes_map[node_id] = resp["id"]
                    all_created_items.append(resp)

        # 4. Draw Connectors in parallel
        connectors_to_create = []
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            if from_id in created_nodes_map and to_id in created_nodes_map:
                start_miro_id = created_nodes_map[from_id]
                end_miro_id = created_nodes_map[to_id]
                caption = conn.get("protocol", "")
                if conn.get("label"):
                    caption = f"{caption}: {conn.get('label')}" if caption else conn.get("label")

                connectors_to_create.append({
                    "start_id": start_miro_id,
                    "end_id": end_miro_id,
                    "caption": caption[:45] if caption else ""
                })

        def create_single_conn(task):
            try:
                return self.create_connector(
                    start_id=task["start_id"],
                    end_id=task["end_id"],
                    caption=task["caption"]
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
