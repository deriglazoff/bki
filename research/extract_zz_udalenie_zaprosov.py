#!/usr/bin/env python3
"""Strict substring match of Исх phrases → ЗЗ / Удаление запросов КИ.

Walks task-pdfs/ and run/. Collapses whitespace (OCR line wraps), then
requires the phrase as a contiguous substring. Case-sensitive.

Usage:
    python research/extract_zz_udalenie_zaprosov.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPORA = (ROOT / "task-pdfs", ROOT / "run")
OUT_DIR = Path(__file__).resolve().parent
HITS_CSV = OUT_DIR / "zz-udalenie-zaprosov-hits.csv"
TASKS_TXT = OUT_DIR / "zz-udalenie-zaprosov-tasks.txt"
TASKS_SPECIFIC_TXT = OUT_DIR / "zz-udalenie-zaprosov-tasks-specific.txt"
BROAD_PHRASE = "правомерность запроса"

# Duplicate rows kept as in the request; matching is per unique phrase.
PHRASES: tuple[tuple[str, str], ...] = (
    ("В случае правомерности выполнения указанных запросов", "Удаление запросов КИ"),
    ("Согласие на запрос кредитной истории не давал", "Удаление запросов КИ"),
    ("Прошу подтвердить правомерность запроса кредитного отчета субъекта", "Удаление запросов КИ"),
    ("правомерность запроса", "Удаление запросов КИ"),
    ("выполнил запрос кредитного отчета указанного субъекта", "Удаление запросов КИ"),
    ("Оспариваемые запросы", "Удаление запросов КИ"),
    ("Согласие на запрос кредитной истории не давал", "Удаление запросов КИ"),
    ("Прошу подтвердить правомерность запроса кредитного отчета", "Удаление запросов КИ"),
)

WS_RE = re.compile(r"\s+")
PAGE_RE = re.compile(r"===== стр\. \d+ =====")


def is_ishod_txt(path: Path) -> bool:
    name = path.name
    lower = name.lower()
    if not lower.endswith(".txt"):
        return False
    if name.startswith("ИСХ") or lower.startswith("исх") or lower == "ishod.txt":
        return True
    if name.startswith("Запрос_"):
        return True
    if lower.startswith("correction_file"):
        return True
    return False


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def collapse(text: str) -> str:
    text = PAGE_RE.sub(" ", text).replace("\u00a0", " ")
    return WS_RE.sub(" ", text)


def unique_phrases() -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for phrase, subtype in PHRASES:
        if phrase in seen:
            continue
        seen.add(phrase)
        out.append((phrase, subtype))
    return out


def file_kind(name: str) -> str:
    lower = name.lower()
    if name.startswith("Запрос_"):
        return "okb"
    if lower.startswith("correction_file"):
        return "skb"
    return "nbki_ishod"


def main() -> None:
    phrases = unique_phrases()
    hits: list[dict[str, str]] = []
    tasks: dict[str, set[str]] = {}
    files_scanned = 0
    phrase_files = {p: 0 for p, _ in phrases}

    for corpus in CORPORA:
        if not corpus.is_dir():
            continue
        corpus_name = corpus.name
        for path in corpus.rglob("*.txt"):
            if not is_ishod_txt(path):
                continue
            files_scanned += 1
            task_id = path.parent.name
            if not task_id.isdigit():
                continue
            blob = collapse(read_text(path))
            matched = [p for p, _ in phrases if p in blob]
            if not matched:
                continue
            kind = file_kind(path.name)
            rel = path.relative_to(ROOT).as_posix()
            for phrase in matched:
                subtype = next(s for p, s in phrases if p == phrase)
                phrase_files[phrase] += 1
                hits.append(
                    {
                        "task_id": task_id,
                        "corpus": corpus_name,
                        "kind": kind,
                        "phrase": phrase,
                        "subtype": subtype,
                        "file": rel,
                    }
                )
            tasks.setdefault(task_id, set()).update(matched)

    hits.sort(key=lambda r: (int(r["task_id"]), r["phrase"], r["file"]))
    task_ids = sorted(tasks, key=int)

    with HITS_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["task_id", "corpus", "kind", "phrase", "subtype", "file"],
        )
        w.writeheader()
        w.writerows(hits)

    TASKS_TXT.write_text(
        "\n".join(task_ids) + ("\n" if task_ids else ""),
        encoding="utf-8",
    )
    specific_ids = sorted(
        (tid for tid, ps in tasks.items() if ps - {BROAD_PHRASE}),
        key=int,
    )
    TASKS_SPECIFIC_TXT.write_text(
        "\n".join(specific_ids) + ("\n" if specific_ids else ""),
        encoding="utf-8",
    )

    print(f"ishod txt scanned: {files_scanned}")
    print(f"hit rows: {len(hits)}")
    print(f"unique tasks (any phrase): {len(task_ids)}")
    print(f"unique tasks excluding only '{BROAD_PHRASE}': {len(specific_ids)}")
    print("per phrase (file hits):")
    for phrase, _ in phrases:
        print(f"  {phrase_files[phrase]:5}  {phrase}")
    print(f"wrote {HITS_CSV.relative_to(ROOT)}")
    print(f"wrote {TASKS_TXT.relative_to(ROOT)}")
    print(f"wrote {TASKS_SPECIFIC_TXT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
