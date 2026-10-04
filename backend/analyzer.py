import os
import shutil
import tempfile
import io
import zipfile
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

IGNORED_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "__pycache__",
    ".venv", "venv", "target", ".idea", ".vscode", "coverage", ".pytest_cache"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".lock", ".pyc", ".min.js", ".min.css", ".map",
    ".pkl", ".pickle", ".h5", ".pt", ".pth", ".bin", ".onnx", ".joblib",
    ".npy", ".npz", ".parquet", ".feather", ".db", ".sqlite", ".sqlite3",
    ".csv", ".tsv", ".log", ".txt", ".md"
}

KEY_CONFIG_FILES = {
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "openapi.yaml",
    "openapi.json", "prisma.schema", "schema.prisma"
}

class CodebaseAnalyzer:
    """Scans and extracts structural architecture signatures from codebases."""

    @staticmethod
    def scan_directory(root_path: str, max_files: int = 120, max_file_size_kb: int = 40) -> Dict[str, Any]:
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
                if ext in IGNORED_EXTENSIONS and fname not in KEY_CONFIG_FILES:
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
                    "router", "controller", "api", "service", "model", "schema",
                    "main.", "app.", "server.", "index."
                ]) and ext in [".py", ".ts", ".js", ".go", ".rs", ".java", ".prisma", ".json", ".yml", ".yaml"]

                if (is_key_config or is_entry_or_route) and len(key_files_content) < 14:
                    try:
                        size_kb = full_path.stat().st_size / 1024
                        if size_kb <= max_file_size_kb:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                if len(content.strip()) > 0:
                                    # Keep concise summary of entry files
                                    if len(content) > 1200:
                                        content = content[:1200] + "\n... [truncated]"
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
        """Clones or downloads a GitHub repository and scans its structure."""
        temp_dir = tempfile.mkdtemp(prefix="qwen_repo_")
        try:
            clean_url = repo_url.strip().rstrip("/")
            if clean_url.endswith(".git"):
                clean_url = clean_url[:-4]

            # Parse GitHub owner/repo: e.g. https://github.com/owner/repo
            match = re.search(r"github\.com/([^/]+)/([^/]+)", clean_url)
            downloaded = False

            if match:
                owner, repo = match.group(1), match.group(2)
                # Try downloading zip archive directly (works on serverless without git CLI)
                for branch in ["main", "master"]:
                    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                    try:
                        resp = requests.get(zip_url, headers={"User-Agent": "QwenArch-Scanner"}, timeout=15)
                        if resp.status_code == 200:
                            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                                z.extractall(temp_dir)
                            downloaded = True
                            break
                    except Exception:
                        pass

            # Fallback to git clone if zip download failed and git is installed
            if not downloaded:
                try:
                    import subprocess
                    clone_target = clean_url + ".git"
                    subprocess.run(["git", "clone", "--depth", "1", clone_target, temp_dir], check=True, capture_output=True, timeout=30)
                    downloaded = True
                except Exception as e:
                    if not downloaded:
                        raise RuntimeError(f"Could not clone or download repository '{repo_url}': {e}")

            # Find the actual root directory (if extracted from zip, it will be inside a subfolder like repo-main)
            subdirs = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            scan_target = subdirs[0] if len(subdirs) == 1 and not (Path(temp_dir) / "package.json").exists() else temp_dir

            result = CodebaseAnalyzer.scan_directory(scan_target)
            result["repo_url"] = repo_url
            return result
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
