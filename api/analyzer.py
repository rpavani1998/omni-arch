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

# Secret and Credential Redaction Patterns
SECRET_PATTERNS = [
    (re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE), '[REDACTED_AWS_KEY]'),
    (re.compile(r'ghp_[0-9a-zA-Z]{36}', re.IGNORECASE), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'sk-[0-9a-zA-Z]{20,}', re.IGNORECASE), '[REDACTED_OPENAI_KEY]'),
    (re.compile(r'(?:bearer\s+)[a-zA-Z0-9_\-\.]{25,}', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
    (re.compile(r'(?:postgres|mysql|mongodb|redis):\/\/[^:\s]+:[^@\s]+@[^\/\s]+', re.IGNORECASE), '[REDACTED_DB_CONNECTION_STRING]'),
    (re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
    (re.compile(r'(password|secret|api_key|access_token|private_key)\s*[:=]\s*["\'][^"\']{6,}["\']', re.IGNORECASE), r'\1: "[REDACTED_SECRET]"')
]

def redact_secrets(text: str) -> str:
    """Scrubs passwords, tokens, API keys, and connection strings from text."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized

def extract_architectural_signatures(content: str, ext: str) -> Dict[str, List[str]]:
    """Extracts high-signal structural signatures (endpoints, models, brokers, clients)."""
    signatures: Dict[str, List[str]] = {
        "routes": [],
        "models": [],
        "services_and_clients": []
    }
    
    # 1. Route and Endpoint Extractor (Python, JS/TS, Go, Java)
    route_patterns = [
        re.compile(r'@(?:app|router|api)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'(?:app|router)\.(get|post|put|delete|patch|use)\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)', re.IGNORECASE),
        re.compile(r'\.(?:GET|POST|PUT|DELETE|PATCH)\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'path\(\s*["\']([^"\']+)["\']', re.IGNORECASE)
    ]
    for pattern in route_patterns:
        for match in pattern.finditer(content):
            groups = match.groups()
            if len(groups) == 2:
                signatures["routes"].append(f"{groups[0].upper()} {groups[1]}")
            elif len(groups) == 1:
                signatures["routes"].append(f"{groups[0].upper()}")

    # 2. Schema and Data Models Extractor
    model_patterns = [
        re.compile(r'class\s+([A-Za-z0-9_]+)\s*\((?:BaseModel|Base|models\.Model|db\.Model|Entity)\)', re.IGNORECASE),
        re.compile(r'model\s+([A-Za-z0-9_]+)\s*\{', re.IGNORECASE),
        re.compile(r'type\s+([A-Za-z0-9_]+)\s+struct\s*\{', re.IGNORECASE),
        re.compile(r'interface\s+([A-Za-z0-9_]+(?:Schema|Model|Entity|DTO|Type|Payload))', re.IGNORECASE)
    ]
    for pattern in model_patterns:
        for match in pattern.finditer(content):
            signatures["models"].append(match.group(1))

    # 3. Infrastructure & External Services Extractor
    client_indicators = [
        ("Redis", re.compile(r'\b(?:redis\.Redis|createClient|getRedisClient|RedisStore)\b', re.IGNORECASE)),
        ("Kafka", re.compile(r'\b(?:KafkaProducer|KafkaConsumer|KafkaClient|KafkaJs)\b', re.IGNORECASE)),
        ("RabbitMQ", re.compile(r'\b(?:pika\.|amqp|amqplib|RabbitMQ)\b', re.IGNORECASE)),
        ("AWS S3", re.compile(r'\b(?:boto3\.client\(["\']s3["\']|@aws-sdk/client-s3)\b', re.IGNORECASE)),
        ("AWS SQS", re.compile(r'\b(?:boto3\.client\(["\']sqs["\']|@aws-sdk/client-sqs)\b', re.IGNORECASE)),
        ("Stripe", re.compile(r'\b(?:stripe\.|@stripe/stripe-js|StripeClient)\b', re.IGNORECASE)),
        ("OpenAI", re.compile(r'\b(?:OpenAI\(|ChatOpenAI|openai\.)\b', re.IGNORECASE)),
        ("PostgreSQL", re.compile(r'\b(?:pg|psycopg2|asyncpg|postgres)\b', re.IGNORECASE)),
        ("Prisma", re.compile(r'\b(?:PrismaClient|prisma\.)\b', re.IGNORECASE)),
        ("Elasticsearch", re.compile(r'\b(?:Elasticsearch|esClient)\b', re.IGNORECASE)),
        ("Celery", re.compile(r'\b(?:Celery\(|@app\.task|shared_task)\b', re.IGNORECASE))
    ]
    for name, regex in client_indicators:
        if regex.search(content):
            signatures["services_and_clients"].append(name)

    # Deduplicate lists
    signatures["routes"] = list(dict.fromkeys(signatures["routes"]))[:15]
    signatures["models"] = list(dict.fromkeys(signatures["models"]))[:12]
    signatures["services_and_clients"] = list(dict.fromkeys(signatures["services_and_clients"]))[:10]
    return signatures

class CodebaseAnalyzer:
    """Scans and extracts structural architecture signatures and AST summaries from codebases."""

    @staticmethod
    def scan_directory(root_path: str, max_files: int = 150, max_file_size_kb: int = 50) -> Dict[str, Any]:
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        file_tree: List[str] = []
        key_files_content: Dict[str, str] = {}
        total_files = 0
        languages: Dict[str, int] = {}
        
        aggregated_routes: List[str] = []
        aggregated_models: List[str] = []
        aggregated_integrations: List[str] = []

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

                if ext:
                    languages[ext] = languages.get(ext, 0) + 1

                full_path = Path(dirpath) / fname
                is_key_config = fname in KEY_CONFIG_FILES
                is_entry_or_route = any(k in rel_path.lower() for k in [
                    "router", "controller", "api", "service", "model", "schema",
                    "main.", "app.", "server.", "index.", "worker.", "queue.", "events."
                ]) and ext in [".py", ".ts", ".js", ".go", ".rs", ".java", ".prisma", ".json", ".yml", ".yaml"]

                if (is_key_config or is_entry_or_route) and len(key_files_content) < 16:
                    try:
                        size_kb = full_path.stat().st_size / 1024
                        if size_kb <= max_file_size_kb:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                raw_content = f.read()
                                if len(raw_content.strip()) > 0:
                                    sanitized = redact_secrets(raw_content)
                                    # Extract structural signatures
                                    sigs = extract_architectural_signatures(sanitized, ext)
                                    aggregated_routes.extend(sigs["routes"])
                                    aggregated_models.extend(sigs["models"])
                                    aggregated_integrations.extend(sigs["services_and_clients"])

                                    if len(sanitized) > 1200:
                                        sanitized = sanitized[:1200] + "\n... [truncated]"
                                    key_files_content[rel_path] = sanitized
                    except Exception:
                        pass

        file_tree = sorted(file_tree)[:max_files]

        return {
            "root_name": root.name,
            "total_files_scanned": total_files,
            "languages": languages,
            "file_tree": file_tree,
            "key_files": key_files_content,
            "signatures": {
                "discovered_routes": list(dict.fromkeys(aggregated_routes))[:20],
                "discovered_models": list(dict.fromkeys(aggregated_models))[:15],
                "discovered_integrations": list(dict.fromkeys(aggregated_integrations))[:10]
            }
        }

    @staticmethod
    def fetch_github_repo(repo_url: str, github_token: Optional[str] = None) -> Dict[str, Any]:
        clean_url = repo_url.strip().rstrip("/")
        if not clean_url.startswith("http"):
            clean_url = f"https://github.com/{clean_url}"

        match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", clean_url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {repo_url}. Expected format: owner/repo or https://github.com/owner/repo")

        owner, repo = match.group(1), match.group(2).replace(".git", "")
        temp_dir = tempfile.mkdtemp(prefix="omniarch_repo_")

        try:
            downloaded = False
            headers = {"User-Agent": "OmniArch-Scanner"}
            if github_token:
                headers["Authorization"] = f"Bearer {github_token}"

            for branch in ["main", "master"]:
                zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                try:
                    resp = requests.get(zip_url, headers=headers, timeout=15)
                    if resp.status_code == 200:
                        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                            z.extractall(temp_dir)
                        downloaded = True
                        break
                except Exception:
                    pass

            if not downloaded:
                try:
                    import subprocess
                    clone_target = clean_url + ".git"
                    subprocess.run(["git", "clone", "--depth", "1", clone_target, temp_dir], check=True, capture_output=True, timeout=30)
                    downloaded = True
                except Exception as e:
                    if not downloaded:
                        raise RuntimeError(f"Could not clone or download repository '{repo_url}': {e}")

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

def analyze_codebase(source_type: str, source_value: str, github_token: Optional[str] = None) -> Dict[str, Any]:
    """Helper function to analyze codebase either from local path or GitHub URL."""
    if source_type == "github":
        return CodebaseAnalyzer.fetch_github_repo(source_value, github_token=github_token)
    else:
        res = CodebaseAnalyzer.scan_directory(source_value)
        res["source_type"] = "local"
        res["source_value"] = source_value
        return res
