#!/usr/bin/env python3
"""Download PDF attachments from Bitrix task descriptions listed in osparivanie-2026-tasks.csv."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

import requests

from scripts.b24 import load_webhook

ROOT = Path(r"C:\repos\bki")
CSV_PATH = ROOT / "osparivanie-2026-tasks.csv"
OUT_DIR = ROOT / "task-pdfs"
MANIFEST_PATH = OUT_DIR / "manifest.csv"
STATE_PATH = OUT_DIR / "_state.json"
BATCH_SIZE = 50
SELECT = ["ID", "TITLE", "DESCRIPTION", "UF_TASK_WEBDAV_FILES"]
DISK_FILE_RE = re.compile(r"DISK\s+FILE\s+ID=(\d+)", re.I)
ATTACHED_ID_RE = re.compile(r"attachedId=(\d+)", re.I)
INVALID_WIN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def batch_call(session: requests.Session, webhook: str, cmd: dict[str, str], retries: int = 5) -> dict:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session.post(webhook + "batch", json={"halt": 0, "cmd": cmd}, timeout=120)
            if resp.status_code == 503 or resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("error"):
                raise RuntimeError(f"{payload.get('error')}: {payload.get('error_description')}")
            return payload.get("result") or payload
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"batch failed after retries: {last_err}")


def task_cmd(task_id: str) -> str:
    params = [("taskId", task_id)]
    for i, field in enumerate(SELECT):
        params.append((f"select[{i}]", field))
    return "tasks.task.get?" + urlencode(params)


def attached_cmd(file_id: str) -> str:
    return "disk.attachedObject.get?" + urlencode({"id": file_id})


def collect_file_ids(task: dict) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()

    def add(raw) -> None:
        if raw in (None, "", False, "false"):
            return
        if isinstance(raw, list):
            for item in raw:
                add(item)
            return
        value = str(raw).strip()
        if value.isdigit() and value not in seen:
            seen.add(value)
            ids.append(value)

    add(task.get("ufTaskWebdavFiles") or task.get("UF_TASK_WEBDAV_FILES"))
    description = task.get("description") or task.get("DESCRIPTION") or ""
    for match in DISK_FILE_RE.finditer(description):
        add(match.group(1))
    for match in ATTACHED_ID_RE.finditer(description):
        add(match.group(1))
    return ids


def safe_name(name: str, file_id: str) -> str:
    name = (name or f"file_{file_id}.pdf").replace("\u00a0", " ").strip()
    name = INVALID_WIN.sub("_", name)
    name = name.rstrip(" .")
    stem, ext = os.path.splitext(name)
    if not ext:
        ext = ".pdf"
    stem = (stem or f"file_{file_id}")[:120]
    return f"{stem}{ext}"


def is_pdf(name: str, content_type: str = "") -> bool:
    name = (name or "").lower()
    content_type = (content_type or "").lower()
    return name.endswith(".pdf") or "pdf" in content_type


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"tasks": {}, "files": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def download_one(session: requests.Session, url: str, dest: Path, expected_size: int | None) -> tuple[str, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and expected_size and dest.stat().st_size == expected_size:
        return "exists", dest.stat().st_size
    tmp = dest.with_suffix(dest.suffix + ".part")
    with session.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "")
        with tmp.open("wb") as fh:
            for chunk in resp.iter_content(64 * 1024):
                if chunk:
                    fh.write(chunk)
    size = tmp.stat().st_size
    if size < 20:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("empty download")
    with tmp.open("rb") as fh:
        magic = fh.read(8)
    if not magic.startswith(b"%PDF") and dest.suffix.lower() == ".pdf":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"not a pdf, magic={magic!r} type={ctype}")
    tmp.replace(dest)
    return "downloaded", size


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    webhook = load_webhook()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        tasks = list(csv.DictReader(fh, delimiter=";"))
    task_ids = [row["task_id"] for row in tasks]
    print(f"tasks in csv: {len(task_ids)}", flush=True)

    session = requests.Session()
    session.headers["User-Agent"] = "bki-task-pdf-export/1.0"
    state = load_state()

    # Phase 1: task metadata
    pending_tasks = [tid for tid in task_ids if tid not in state["tasks"]]
    print(f"tasks to fetch: {len(pending_tasks)}", flush=True)
    fetched = 0
    for batch_ids in chunks(pending_tasks, BATCH_SIZE):
        cmd = {f"t{tid}": task_cmd(tid) for tid in batch_ids}
        result = batch_call(session, webhook, cmd)
        results = result.get("result") or {}
        errors = result.get("result_error") or {}
        for tid in batch_ids:
            key = f"t{tid}"
            if key in errors and errors[key]:
                state["tasks"][tid] = {"error": str(errors[key]), "file_ids": []}
                continue
            raw = results.get(key) or {}
            task = raw.get("task") if isinstance(raw, dict) else None
            if not task:
                state["tasks"][tid] = {"error": "empty", "file_ids": []}
                continue
            file_ids = collect_file_ids(task)
            state["tasks"][tid] = {
                "title": task.get("title") or "",
                "file_ids": file_ids,
            }
        fetched += len(batch_ids)
        if fetched % 200 == 0 or fetched == len(pending_tasks):
            save_state(state)
            print(f"tasks fetched: {fetched}/{len(pending_tasks)}", flush=True)
        time.sleep(0.15)
    save_state(state)

    attachments: list[tuple[str, str]] = []
    for tid, meta in state["tasks"].items():
        for fid in meta.get("file_ids") or []:
            attachments.append((tid, str(fid)))
    print(f"attached ids: {len(attachments)}", flush=True)

    # Phase 2: attached object metadata
    pending_files = [
        (tid, fid)
        for tid, fid in attachments
        if fid not in state["files"] or not state["files"][fid].get("download_url")
    ]
    print(f"file metas to fetch: {len(pending_files)}", flush=True)
    done_meta = 0
    unique_pending = []
    seen_fid = set()
    for tid, fid in pending_files:
        if fid not in seen_fid:
            seen_fid.add(fid)
            unique_pending.append(fid)
    for batch_fids in chunks(unique_pending, BATCH_SIZE):
        cmd = {f"f{fid}": attached_cmd(fid) for fid in batch_fids}
        result = batch_call(session, webhook, cmd)
        results = result.get("result") or {}
        errors = result.get("result_error") or {}
        for fid in batch_fids:
            key = f"f{fid}"
            if key in errors and errors[key]:
                state["files"][fid] = {"error": str(errors[key])}
                continue
            raw = results.get(key) or {}
            if not isinstance(raw, dict) or not raw.get("DOWNLOAD_URL"):
                state["files"][fid] = {"error": f"no url: {raw!r}"[:300]}
                continue
            state["files"][fid] = {
                "name": raw.get("NAME") or f"file_{fid}.pdf",
                "size": int(raw.get("SIZE") or 0),
                "download_url": raw["DOWNLOAD_URL"],
                "object_id": str(raw.get("OBJECT_ID") or ""),
                "entity_id": str(raw.get("ENTITY_ID") or ""),
            }
        done_meta += len(batch_fids)
        if done_meta % 200 == 0 or done_meta == len(unique_pending):
            save_state(state)
            print(f"file metas: {done_meta}/{len(unique_pending)}", flush=True)
        time.sleep(0.15)
    save_state(state)

    # Phase 3: download PDFs
    jobs = []
    for tid, fid in attachments:
        meta = state["files"].get(fid) or {}
        name = meta.get("name") or ""
        url = meta.get("download_url")
        if meta.get("error") or not url:
            jobs.append(
                {
                    "task_id": tid,
                    "file_id": fid,
                    "name": name,
                    "status": "meta_error",
                    "error": meta.get("error", "no url"),
                    "path": "",
                    "size": 0,
                }
            )
            continue
        if not is_pdf(name):
            jobs.append(
                {
                    "task_id": tid,
                    "file_id": fid,
                    "name": name,
                    "status": "skipped_not_pdf",
                    "error": "",
                    "path": "",
                    "size": int(meta.get("size") or 0),
                }
            )
            continue
        filename = safe_name(name, fid)
        dest = OUT_DIR / tid / filename
        jobs.append(
            {
                "task_id": tid,
                "file_id": fid,
                "name": name,
                "status": "pending",
                "error": "",
                "path": str(dest),
                "size": int(meta.get("size") or 0),
                "url": url,
                "dest": dest,
            }
        )

    to_download = [j for j in jobs if j["status"] == "pending"]
    print(f"pdfs to download: {len(to_download)}", flush=True)

    def worker(job: dict) -> dict:
        dl_session = requests.Session()
        dl_session.headers["User-Agent"] = "bki-task-pdf-export/1.0"
        try:
            status, size = download_one(dl_session, job["url"], job["dest"], job["size"] or None)
            job["status"] = status
            job["size"] = size
        except Exception as exc:  # noqa: BLE001
            job["status"] = "error"
            job["error"] = str(exc)[:300]
        job.pop("url", None)
        job.pop("dest", None)
        return job

    completed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(worker, job) for job in to_download]
        for fut in as_completed(futures):
            fut.result()
            completed += 1
            if completed % 100 == 0 or completed == len(to_download):
                print(f"downloaded: {completed}/{len(to_download)}", flush=True)

    fieldnames = ["task_id", "file_id", "name", "status", "size", "path", "error"]
    with MANIFEST_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for job in jobs:
            writer.writerow({k: job.get(k, "") for k in fieldnames})

    counts: dict[str, int] = {}
    for job in jobs:
        counts[job["status"]] = counts.get(job["status"], 0) + 1
    tasks_with_pdf = len({j["task_id"] for j in jobs if j["status"] in {"downloaded", "exists"}})
    tasks_no_files = sum(1 for meta in state["tasks"].values() if not meta.get("file_ids"))
    print("=== summary ===", flush=True)
    print(f"tasks: {len(task_ids)}", flush=True)
    print(f"tasks without attachments: {tasks_no_files}", flush=True)
    print(f"tasks with saved pdf: {tasks_with_pdf}", flush=True)
    print(f"statuses: {counts}", flush=True)
    print(f"out: {OUT_DIR}", flush=True)
    print(f"manifest: {MANIFEST_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
