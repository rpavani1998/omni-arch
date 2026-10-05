import os
import json
import sys
import re
import subprocess
import requests

def check_architectural_changes_in_pr() -> bool:
    """Returns True if files modified in the PR have potential architectural impact."""
    try:
        base_ref = os.getenv("GITHUB_BASE_REF") or "main"
        # Fetch base branch diff if available
        res = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
            capture_output=True,
            text=True,
            timeout=10
        )
        changed_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        if not changed_files:
            # Fallback to HEAD~1 diff
            res = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1...HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            changed_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        
        if not changed_files:
            return True  # If git history unavailable, proceed safely
            
        architectural_exts = {".py", ".ts", ".js", ".go", ".rs", ".java", ".prisma", ".sql", ".graphql"}
        key_manifests = {
            "package.json", "requirements.txt", "pyproject.toml", "go.mod", 
            "Cargo.toml", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            "openapi.yaml", "openapi.json"
        }
        
        for f in changed_files:
            fname = os.path.basename(f)
            ext = os.path.splitext(f)[1].lower()
            
            # Explicitly ignore non-architectural documentation, test suites, and styling
            if any(f.startswith(d) for d in ["docs/", "tests/", "frontend/public/", ".github/"]):
                continue
            if ext in [".md", ".txt", ".png", ".jpg", ".svg", ".css", ".ico", ".lock"]:
                continue
            if fname in key_manifests or ext in architectural_exts:
                return True
        return False
    except Exception as e:
        print(f"[Pre-Flight] Diff inspection warning: {e}. Proceeding with standard scan.")
        return True

def main():
    # Load OmniArch action modules from action checkout path
    action_root = os.getenv("ACTION_PATH") or os.getcwd()
    sys.path.insert(0, action_root)
    
    skip_unchanged = os.getenv("INPUT_SKIP_UNCHANGED", "true").lower() in ("true", "1", "yes")
    is_pr = bool(os.getenv("GITHUB_BASE_REF") or (os.getenv("GITHUB_REF", "").startswith("refs/pull/")))
    
    # 0. Pre-Flight Zero-Cost Early Exit
    if skip_unchanged and is_pr:
        if not check_architectural_changes_in_pr():
            print("[Pre-Flight] No architectural file modifications detected in this PR. Skipping AI synthesis and Miro sync ($0 token cost).")
            if "GITHUB_STEP_SUMMARY" in os.environ and os.environ["GITHUB_STEP_SUMMARY"]:
                try:
                    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as sf:
                        sf.write("### ⚡ OmniArch Pre-Flight Optimization\n")
                        sf.write("- **Status:** Skipped (No structural architecture files modified in this PR).\n")
                        sf.write("- **Token Cost:** $0.00 | **Latency:** < 1s\n")
                except Exception:
                    pass
            return

    from backend.analyzer import analyze_codebase
    from backend.engine import ArchitectureEngine
    from backend.miro_client import MiroClient
    
    target_dir = os.getcwd()
    print(f"[1/4] Ingesting codebase directory from {target_dir}...")
    codebase_data = analyze_codebase(source_type="local", source_value=target_dir)
    
    perspective = os.getenv("INPUT_PERSPECTIVE", "overview")
    print(f"[2/4] Running AI architectural synthesis (Perspective: {perspective})...")
    engine = ArchitectureEngine()
    arch_data = engine.generate_architecture(
        codebase_data=codebase_data,
        provider=os.getenv("INPUT_PROVIDER", "custom"),
        api_key=os.getenv("INPUT_API_KEY") or None,
        base_url=os.getenv("INPUT_BASE_URL") or None,
        model_name=os.getenv("INPUT_MODEL_NAME") or None,
        perspective=perspective,
        custom_instructions=os.getenv("INPUT_CUSTOM_INSTRUCTIONS", "")
    )
    
    miro_token = os.getenv("MIRO_ACCESS_TOKEN")
    miro_board = os.getenv("MIRO_BOARD_ID")
    
    if miro_token and miro_board:
        print(f"[3/4] Synchronizing to Miro Board: {miro_board}...")
        client = MiroClient(
            access_token=miro_token,
            board_id=miro_board
        )
        sync_result = client.sync_architecture_diagram(
            arch_data=arch_data,
            perspective=perspective
        )
        board_url = sync_result.get("board_url", "")
        frame_id = sync_result.get("frame_id", "")
        print(f"[SUCCESS] Miro Frame Sync Complete! Deep Link: {board_url}")
    else:
        print("[3/4] [INFO] MIRO_ACCESS_TOKEN or MIRO_BOARD_ID not provided. Generating architecture preview in offline mode.")
        sync_result = {
            "success": True,
            "created_nodes": len(arch_data.get("nodes", [])),
            "updated_nodes": 0,
            "deleted_nodes": 0,
            "total_items": len(arch_data.get("nodes", [])),
            "frame_title": f"System Architecture ({perspective})",
            "board_url": "https://miro.com (Offline Mode - set MIRO_ACCESS_TOKEN to sync live)",
            "frame_id": "offline_mode"
        }
        board_url = sync_result["board_url"]
        frame_id = sync_result["frame_id"]

    print("[4/4] Checking Architectural Drift & Review Reporting...")
    
    created = sync_result.get("created_nodes", 0)
    updated = sync_result.get("updated_nodes", 0)
    deleted = sync_result.get("deleted_nodes", 0)
    
    is_major = (created > 0 and sync_result.get("sync_mode") == "incremental_update") or deleted > 0
    if is_major:
        badge = "CRITICAL: ARCHITECTURE REVIEW REQUIRED"
        headline = "Major Architectural Changes Detected in this PR"
        action_prompt = "Architectural boundaries or services were added/removed. Please review the updated Miro diagram before merging."
    elif updated > 0 or created > 0:
        badge = "ARCHITECTURE UPDATED IN-PLACE"
        headline = "Architecture Components Updated In-Place"
        action_prompt = "Existing service descriptions, endpoints, or dependencies have been synchronized to Miro."
    else:
        badge = "NO TOPOLOGICAL DRIFT"
        headline = "No Structural Architecture Changes"
        action_prompt = "Architecture diagram is up to date with this commit."
    
    frame_title = sync_result.get("frame_title", "System Architecture")
    nodes = arch_data.get("nodes", [])
    layers = arch_data.get("layers", [])
    connections = arch_data.get("connections", [])
    insights = arch_data.get("insights", {})
    
    node_rows = []
    for n in nodes[:8]:
        ntype = n.get("type", "service").upper()
        nname = n.get("name", "Component")
        ntech = n.get("tech", "N/A")
        node_rows.append(f"| `{ntype}` | **{nname}** | {ntech} |")
    node_table = "\n".join(node_rows) if node_rows else "| `SERVICE` | **Application Service** | Core |"
    
    # Build native GitHub-rendered Mermaid diagram
    def sanitize_id(raw_id: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(raw_id))

    mermaid_lines = ["```mermaid", "graph TD"]
    for l in layers:
        lid = sanitize_id(l.get("id", "tier"))
        lname = l.get("name", "Tier").replace('"', "'")
        mermaid_lines.append(f'  subgraph {lid} ["{lname}"]')
        for n in nodes:
            if n.get("layer_id") == l.get("id"):
                nid = sanitize_id(n.get("id", "node"))
                nname = n.get("name", "Component").replace('"', "'")
                ntech = n.get("tech", "").replace('"', "'")
                label = f"{nname}<br/>({ntech})" if ntech else nname
                mermaid_lines.append(f'    {nid}["{label}"]')
        mermaid_lines.append("  end")

    for c in connections:
        c_from = sanitize_id(c.get("from", ""))
        c_to = sanitize_id(c.get("to", ""))
        clabel = c.get("label") or c.get("protocol") or ""
        if clabel:
            clabel_clean = clabel.replace('"', "'")
            mermaid_lines.append(f'  {c_from} -->|"{clabel_clean}"| {c_to}')
        else:
            mermaid_lines.append(f'  {c_from} --> {c_to}')
    mermaid_lines.append("```")
    mermaid_block = "\n".join(mermaid_lines)

    strengths = "<br/>• ".join(insights.get("strengths", ["Modular design", "Clear layer separation"])[:2])
    recommendations = "<br/>• ".join(insights.get("recommendations", ["Verify data boundary isolation", "Check API rate limits"])[:2])
    
    comment = f"""<!-- omniarch-pr-architecture-comment -->
## [{badge}] OmniArch Architecture Sync

### {headline}
> {action_prompt}

---

### Interactive Miro Diagram
**Board Frame:** [{frame_title}]({board_url})  
**Live Canvas Link:** [Open in Miro Board]({board_url})

| Perspective | Created Nodes | Updated In-Place | Deleted Nodes | Total Items |
| :--- | :---: | :---: | :---: | :---: |
| **{perspective.replace('_', ' ').title()}** | `{created}` | `{updated}` | `{deleted}` | `{sync_result.get('total_items', len(nodes))}` |

---

### In-PR Architecture Visual (Mermaid)
<details open>
<summary><b>Click to expand live diagram preview</b></summary>

{mermaid_block}

</details>

---

### Discovered Topology ({len(nodes)} components)
| Tier / Type | Component | Technology |
| :--- | :--- | :--- |
{node_table}

---

### Architectural Review Insights
- **Key Strengths:**
  • {strengths}
- **Recommended Review Checklist:**
  • {recommendations}

*Automated by [OmniArch](https://github.com/rpavani1998/omni-arch) & Miro Living Architecture Engine.*
"""
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    ev_path = os.getenv("GITHUB_EVENT_PATH")
    only_on_drift = os.getenv("INPUT_ONLY_ON_DRIFT", "true").lower() in ("true", "1", "yes")
    has_drift = (created > 0 or updated > 0 or deleted > 0)
    
    # Conditional PR comment filtering
    if only_on_drift and not has_drift:
        print("[INFO] No architectural drift detected. Skipping PR comment posting to keep review clean.")
        if "GITHUB_STEP_SUMMARY" in os.environ and os.environ["GITHUB_STEP_SUMMARY"]:
            try:
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as sf:
                    sf.write("### OmniArch Architecture Verification\n")
                    sf.write(f"- **Status:** No Topological Drift detected ({frame_title}).\n")
                    sf.write("- **Miro Board:** Existing diagrams are up to date.\n")
                    sf.write("- **PR Comment:** Skipped per `only-on-drift: true` setting.\n")
            except Exception:
                pass
    elif github_token and repo:
        pr_number = None
        if ev_path and os.path.exists(ev_path):
            try:
                with open(ev_path, "r", encoding="utf-8") as f:
                    event_data = json.load(f)
                    if "pull_request" in event_data:
                        pr_number = event_data["pull_request"]["number"]
                    elif "issue" in event_data:
                        pr_number = event_data["issue"]["number"]
            except Exception as e:
                print(f"[WARN] Could not parse GITHUB_EVENT_PATH: {e}")
        
        if pr_number:
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
            try:
                resp = requests.get(comments_url, headers=headers)
                if resp.status_code == 200:
                    comments = resp.json()
                    commented = False
                    for c in comments:
                        if "<!-- omniarch-pr-architecture-comment -->" in c.get("body", ""):
                            comment_id = c["id"]
                            patch_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
                            p_resp = requests.patch(patch_url, headers=headers, json={"body": comment})
                            if p_resp.status_code in (200, 201):
                                print(f"[SUCCESS] Updated OmniArch PR comment #{comment_id} on PR #{pr_number}")
                                commented = True
                            break
                    if not commented:
                        post_resp = requests.post(comments_url, headers=headers, json={"body": comment})
                        if post_resp.status_code in (200, 201):
                            print(f"[SUCCESS] Posted OmniArch PR comment on PR #{pr_number}")
                        else:
                            print(f"[WARN] Failed to post PR comment: status={post_resp.status_code}")
                else:
                    print(f"[WARN] Failed to fetch PR comments: status={resp.status_code}")
            except Exception as e:
                print(f"[WARN] Error posting PR comment: {e}")
        else:
            print("[INFO] Not a Pull Request event. Skipping PR comment posting.")
    else:
        print("[INFO] GITHUB_TOKEN or GITHUB_REPOSITORY not set. Skipping PR comment.")
    
    # Write outputs to GitHub Action environment
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"board-url={board_url}\n")
            f.write(f"frame-id={frame_id}\n")

if __name__ == "__main__":
    main()
