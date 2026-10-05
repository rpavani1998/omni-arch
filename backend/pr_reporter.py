import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("omniarch.pr_reporter")

class PRArchitectureReporter:
    """
    Automated GitHub Pull Request Reporter for OmniArch.
    Analyzes architectural drift, detects major structural changes,
    and posts or updates sticky PR review comments on GitHub.
    """

    @staticmethod
    def detect_change_severity(sync_result: Dict[str, Any], arch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines if a PR introduces major architectural changes:
        - Major: New services, databases, gateways added or deleted
        - Moderate: Existing services modified in-place
        - Minor: No structural topological changes
        """
        created = sync_result.get("created_nodes", 0)
        updated = sync_result.get("updated_nodes", 0)
        deleted = sync_result.get("deleted_nodes", 0)
        
        # Check if initial creation or if nodes were added/removed
        is_major = (created > 0 and sync_result.get("sync_mode") == "incremental_update") or deleted > 0
        
        if is_major:
            severity = "MAJOR"
            badge = "CRITICAL: ARCHITECTURE REVIEW REQUIRED"
            headline = "Major Architectural Changes Detected in this PR"
            action_prompt = "Architectural boundaries or services were added/removed. Please review the updated Miro diagram before merging."
        elif updated > 0 or created > 0:
            severity = "MODERATE"
            badge = "ARCHITECTURE UPDATED IN-PLACE"
            headline = "Architecture Components Updated In-Place"
            action_prompt = "Existing service descriptions, endpoints, or dependencies have been synchronized to Miro."
        else:
            severity = "MINOR"
            badge = "NO TOPOLOGICAL DRIFT"
            headline = "No Structural Architecture Changes"
            action_prompt = "Architecture diagram is up to date with this commit."

        return {
            "severity": severity,
            "badge": badge,
            "headline": headline,
            "action_prompt": action_prompt,
            "created_nodes": created,
            "updated_nodes": updated,
            "deleted_nodes": deleted
        }

    @classmethod
    def generate_pr_markdown_comment(
        cls, 
        sync_result: Dict[str, Any], 
        arch_data: Dict[str, Any],
        perspective: str = "overview",
        repo_name: Optional[str] = None
    ) -> str:
        """Generates rich markdown for GitHub PR comment."""
        diff_meta = cls.detect_change_severity(sync_result, arch_data)
        board_url = sync_result.get("board_url", "#")
        frame_title = sync_result.get("frame_title", "System Architecture")
        system_title = arch_data.get("system_title", repo_name or "Project")
        
        nodes = arch_data.get("nodes", [])
        insights = arch_data.get("insights", {})
        
        node_rows = []
        for n in nodes[:8]:
            ntype = n.get("type", "service").upper()
            nname = n.get("name", "Component")
            ntech = n.get("tech", "N/A")
            node_rows.append(f"| `{ntype}` | **{nname}** | {ntech} |")

        node_table = "\n".join(node_rows) if node_rows else "| `SERVICE` | **Application Service** | Core |"
        
        strengths = "<br/>• ".join(insights.get("strengths", ["Modular design", "Clear layer separation"])[:2])
        recommendations = "<br/>• ".join(insights.get("recommendations", ["Verify data boundary isolation", "Check API rate limits"])[:2])

        comment = f"""<!-- omniarch-pr-architecture-comment -->
## [{diff_meta['badge']}] OmniArch Architecture Sync

### {diff_meta['headline']}
> {diff_meta['action_prompt']}

---

### Interactive Miro Diagram
**Board Frame:** [{frame_title}]({board_url})
**Live Canvas Link:** [Open in Miro Board]({board_url})

| Perspective | Created Nodes | Updated In-Place | Deleted Nodes | Total Items |
| :--- | :---: | :---: | :---: | :---: |
| **{perspective.replace('_', ' ').title()}** | `{diff_meta['created_nodes']}` | `{diff_meta['updated_nodes']}` | `{diff_meta['deleted_nodes']}` | `{sync_result.get('total_items', len(nodes))}` |

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

*Automated by [OmniArch](https://github.com/rpavani1998/qwen-arch-canvas) & Miro Living Architecture Engine.*
"""
        return comment

    @classmethod
    def post_or_update_pr_comment(
        cls, 
        sync_result: Dict[str, Any], 
        arch_data: Dict[str, Any],
        perspective: str = "overview",
        github_token: Optional[str] = None,
        github_repository: Optional[str] = None,
        event_path: Optional[str] = None
    ) -> bool:
        """Finds active PR from GitHub Actions context and posts or updates the sticky comment."""
        token = github_token or os.getenv("GITHUB_TOKEN")
        repo = github_repository or os.getenv("GITHUB_REPOSITORY")
        ev_path = event_path or os.getenv("GITHUB_EVENT_PATH")
        
        if not token or not repo:
            logger.warning("GITHUB_TOKEN or GITHUB_REPOSITORY not set. Skipping PR comment.")
            return False

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
                logger.warning(f"Could not parse GITHUB_EVENT_PATH: {e}")

        if not pr_number:
            logger.info("Not a Pull Request event. Skipping PR comment posting.")
            return False

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        body_content = cls.generate_pr_markdown_comment(
            sync_result=sync_result,
            arch_data=arch_data,
            perspective=perspective,
            repo_name=repo
        )

        # 1. Search for existing OmniArch comment to update in-place (avoid spamming PRs)
        comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        try:
            resp = requests.get(comments_url, headers=headers)
            if resp.status_code == 200:
                comments = resp.json()
                for c in comments:
                    if "<!-- omniarch-pr-architecture-comment -->" in c.get("body", ""):
                        # Update existing comment
                        comment_id = c["id"]
                        patch_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
                        p_resp = requests.patch(patch_url, headers=headers, json={"body": body_content})
                        if p_resp.status_code in (200, 201):
                            logger.info(f"Successfully updated OmniArch PR comment #{comment_id} on PR #{pr_number}")
                            return True

            # 2. Create new comment if none exists
            post_resp = requests.post(comments_url, headers=headers, json={"body": body_content})
            if post_resp.status_code in (200, 201):
                logger.info(f"Successfully posted OmniArch PR comment on PR #{pr_number}")
                return True
            else:
                logger.error(f"Failed to post PR comment: status={post_resp.status_code} body={post_resp.text}")
        except Exception as e:
            logger.error(f"Error posting PR comment: {e}")
            
        return False
