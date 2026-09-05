#!/usr/bin/env python3
"""Bitrix24 incoming-webhook REST. Agent skills call this instead of Bitrix MCP.

Webhook (first match):
  1. env B24_DEFAULT_WEBHOOK or BITRIX_WEBHOOK_URL
  2. ~/.cursor/mcp.json — mcpServers.*.env.B24_DEFAULT_WEBHOOK
  3. ~/.cursor/mcp.json — args header X-B24-Webhook:...

Usage:
  python scripts/b24.py call METHOD [--json JSON | --file PATH | --stdin]
  python scripts/b24.py download URL OUT_PATH

Long BBCode / nested params: write UTF-8 JSON and pass --file (do not quote in PowerShell).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HEADER_PREFIX = "x-b24-webhook:"
ENV_KEYS = ("B24_DEFAULT_WEBHOOK", "BITRIX_WEBHOOK_URL")


def _normalize_webhook(url: str) -> str:
    url = (url or "").strip().strip('"').strip("'")
    if not url:
        raise RuntimeError("empty Bitrix webhook")
    return url.rstrip("/") + "/"


def _webhook_from_mcp_server(server: dict) -> str | None:
    env_map = server.get("env") or {}
    for key in ENV_KEYS:
        value = env_map.get(key)
        if value:
            return _normalize_webhook(value)
    for i, arg in enumerate(server.get("args") or []):
        if not isinstance(arg, str):
            continue
        lower = arg.lower()
        if lower.startswith(HEADER_PREFIX):
            return _normalize_webhook(arg.split(":", 1)[1])
        if arg == "--header" and i + 1 < len(server["args"]):
            nxt = server["args"][i + 1]
            if isinstance(nxt, str) and nxt.lower().startswith(HEADER_PREFIX):
                return _normalize_webhook(nxt.split(":", 1)[1])
    return None


def load_webhook() -> str:
    for key in ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return _normalize_webhook(value)
    mcp_path = Path.home() / ".cursor" / "mcp.json"
    if not mcp_path.is_file():
        raise RuntimeError(
            "Bitrix webhook not found: set B24_DEFAULT_WEBHOOK or add X-B24-Webhook in ~/.cursor/mcp.json"
        )
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or {}
    preferred = ("bitrix24", "bitrix24-test")
    for name in preferred:
        server = servers.get(name)
        if isinstance(server, dict):
            found = _webhook_from_mcp_server(server)
            if found:
                return found
    for server in servers.values():
        if isinstance(server, dict):
            found = _webhook_from_mcp_server(server)
            if found:
                return found
    raise RuntimeError(
        "Bitrix webhook not found: set B24_DEFAULT_WEBHOOK or add X-B24-Webhook in ~/.cursor/mcp.json"
    )


def rest_call(method: str, payload: dict | None = None, timeout: int = 180) -> dict:
    method = method.strip().lstrip("/")
    if not method:
        raise RuntimeError("empty REST method")
    url = load_webhook() + method
    data = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code} {method}: {detail}") from exc
    if body.get("error"):
        raise RuntimeError(f"{body.get('error')}: {body.get('error_description')}")
    return body


def download(url: str, out_path: Path, timeout: int = 180) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "bki-b24-rest/1.0"})
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code} download: {detail}") from exc
    if len(payload) < 20:
        raise RuntimeError("empty download")
    if "text/html" in ctype and not payload[:8].startswith(b"%PDF"):
        raise RuntimeError("download returned HTML, not a file")
    tmp.write_bytes(payload)
    tmp.replace(out_path)
    return out_path


def _load_payload(args: argparse.Namespace) -> dict:
    sources = [bool(args.json), bool(args.file), bool(args.stdin)]
    if sum(sources) > 1:
        raise RuntimeError("use only one of --json / --file / --stdin")
    if args.json:
        data = json.loads(args.json)
    elif args.file:
        data = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
    elif args.stdin:
        data = json.loads(sys.stdin.read())
    else:
        data = {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RuntimeError("REST params must be a JSON object")
    return data


def _print_json(data: object) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bitrix24 incoming-webhook REST")
    sub = parser.add_subparsers(dest="cmd", required=True)

    call_p = sub.add_parser("call", help="POST webhook METHOD with JSON params")
    call_p.add_argument("method")
    call_p.add_argument("--json", help="JSON object string")
    call_p.add_argument("--file", help="UTF-8 JSON object file")
    call_p.add_argument("--stdin", action="store_true", help="read JSON object from stdin")
    call_p.add_argument("--timeout", type=int, default=180)

    dl_p = sub.add_parser("download", help="GET DOWNLOAD_URL to a local file")
    dl_p.add_argument("url")
    dl_p.add_argument("out")
    dl_p.add_argument("--timeout", type=int, default=180)

    args = parser.parse_args(argv)
    if args.cmd == "call":
        result = rest_call(args.method, _load_payload(args), timeout=args.timeout)
        _print_json(result)
        return 0
    path = download(args.url, Path(args.out), timeout=args.timeout)
    _print_json({"ok": True, "path": str(path), "size": path.stat().st_size})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
