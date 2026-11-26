"""Read-only source inventory. Never imports or starts discovered code."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SKIP = {".git", "node_modules", ".venv", "venv", "site-packages", "__pycache__", "build", "target"}
PATTERNS = {
    "tcp-listener": r"ServerSocket\s*\(|\.listen\s*\(",
    "tcp-client": r"(?:new\s+Socket|socket\.create_connection)\s*\(",
    "udp": r"DatagramSocket\s*\(|SOCK_DGRAM",
    "http": r"HTTPServer|HttpServer\.create|Flask\s*\(|FastAPI\s*\(",
    "desktop-ui": r"JFrame|tkinter|webview\.create_window",
    "pulse-reference": r"\b7\.83\b",
    "tesla-reference": r"\b[Tt][Ee][Ss][Ll][Aa]\b",
    "text-reference": r"\b(?:[Bb]ible|[Qq]uran|[Tt]orah|[Gg]ita|[Tt]ao)\b",
}


def visible_processes():
    command = "$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(java|javaw|python|pythonw|py)(\\d+(\\.\\d+)*)?\\.exe$' } | Select-Object ProcessId,Name,ExecutablePath | ConvertTo-Json -Compress"
    try:
        run = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                             capture_output=True, text=True, timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if run.returncode:
            return {"status": "unavailable", "reason": "Windows process metadata access was denied in this inspection environment.", "processes": []}
        rows = json.loads(run.stdout) if run.stdout.strip() else []
        return {"status": "visible-processes-only", "processes": rows if isinstance(rows, list) else [rows],
                "note": "A source file on disk does not establish that it is running or connected."}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "reason": "Process query failed or timed out.", "processes": []}


def scan(roots):
    files, errors, seen = [], [], set()
    for root in roots:
        if not root.is_dir():
            errors.append({"path": str(root), "error": "Directory not found"})
            continue
        for folder, dirs, names in os.walk(root, followlinks=False, onerror=lambda e: errors.append({"path": e.filename, "error": type(e).__name__})):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP and not d.lower().startswith("backup")]
            for name in sorted(names):
                path = Path(folder) / name
                if path.suffix.lower() not in {".java", ".py"}:
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                try:
                    if path.stat().st_size > 2_000_000:
                        errors.append({"path": str(path), "error": "Source exceeds 2 MB scan limit"})
                        continue
                    raw = path.read_bytes()
                    source = raw.decode("utf-8-sig", errors="replace")
                    item = {"path": str(path), "language": "Python" if path.suffix.lower() == ".py" else "Java",
                            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                            "capabilities": {}, "connection": "not-attached"}
                    for capability, pattern in PATTERNS.items():
                        lines = [i for i, line in enumerate(source.splitlines(), 1) if re.search(pattern, line)]
                        if lines:
                            item["capabilities"][capability] = lines[:12]
                    if item["language"] == "Python":
                        try:
                            tree = ast.parse(source)
                            item["definitions"] = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))][:60]
                            item["syntax"] = "parsed"
                        except SyntaxError as exc:
                            item["syntax"] = f"Syntax error at line {exc.lineno}: {exc.msg}"
                    else:
                        item["definitions"] = re.findall(r"\bclass\s+(\w+)", source)[:60]
                    files.append(item)
                except OSError as exc:
                    errors.append({"path": str(path), "error": type(exc).__name__})
    return {"created_utc": datetime.now(timezone.utc).isoformat(), "roots": list(map(str, roots)),
            "summary": {"source_count": len(files), "languages": dict(Counter(f["language"] for f in files)),
                        "interface_candidates": sum(bool(set(f["capabilities"]) & {"tcp-listener", "tcp-client", "http", "udp"}) for f in files)},
            "notes": ["Static signatures can occur in comments or examples; they are candidates, not live interface checks.",
                      "No discovered source was imported, executed, edited or connected.",
                      "Backups, environments and build folders were excluded."],
            "process_scan": visible_processes(), "files": files, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = scan(args.roots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"]))
    print("Process scan:", report["process_scan"]["status"])


if __name__ == "__main__":
    main()
