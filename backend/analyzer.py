import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import git

IGNORED_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "__pycache__",
    ".venv", "venv", "target", ".idea", ".vscode", "coverage", ".pytest_cache"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".lock", ".pyc", ".min.js", ".min.css", ".map"
}

KEY_CONFIG_FILES = {
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "README.md", "openapi.yaml",
    "openapi.json", "prisma.schema", "schema.prisma"
}

class CodebaseAnalyzer:
    """Scans and extracts structural architecture signatures from codebases."""

    @staticmethod
    def scan_directory(root_path: str, max_files: int = 120, max_file_size_kb: int = 50) -> Dict[str, Any]:
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        file_tree: List[str] = []
        key_files_content: Dict[str, str] = {}
        total_files = 0
        languages: Dict[str, int] = {}

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in-place
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith('.')]
            
            rel_dir = os.path.relpath(dirpath, root)
            if rel_dir == ".":
                rel_dir = ""

            for fname in filenames:
                if fname.startswith('.') and fname != '.env.example':
                    continue
                ext = Path(fname).suffix.lower()
                if ext in IGNORED_EXTENSIONS:
                    continue

                total_files += 1
                rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
                file_tree.append(rel_path)

                # Count languages
                if ext:
                    languages[ext] = languages.get(ext, 0) + 1

                # Capture content of key config and entry files
                full_path = Path(dirpath) / fname
                is_key_config = fname in KEY_CONFIG_FILES
                is_entry_or_route = any(k in rel_path.lower() for k in [
                    "route", "controller", "api", "service", "model", "schema",
                    "main.", "app.", "server.", "index.", "router"
                ])

                if (is_key_config or is_entry_or_route) and len(key_files_content) < 35:
                    try:
                        size_kb = full_path.stat().st_size / 1024
                        if size_kb <= max_file_size_kb:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                if len(content.strip()) > 0:
                                    # Truncate if very long
                                    if len(content) > 3000:
                                        content = content[:3000] + "\n... [truncated]"
                                    key_files_content[rel_path] = content
                    except Exception:
                        pass

        # Sort file tree for clean display
        file_tree = sorted(file_tree)[:max_files]

        return {
            "root_name": root.name,
            "total_files_scanned": total_files,
            "languages": languages,
            "file_tree": file_tree,
            "key_files": key_files_content
        }

    @staticmethod
    def clone_and_scan_github(repo_url: str) -> Dict[str, Any]:
        """Clones a GitHub repository shallowly and scans its structure."""
        temp_dir = tempfile.mkdtemp(prefix="qwen_repo_")
        try:
            # Clean url
            clean_url = repo_url.strip()
            if not clean_url.endswith(".git") and not clean_url.endswith("/"):
                clean_url = clean_url + ".git"

            git.Repo.clone_from(clean_url, temp_dir, depth=1)
            result = CodebaseAnalyzer.scan_directory(temp_dir)
            result["repo_url"] = repo_url
            return result
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
