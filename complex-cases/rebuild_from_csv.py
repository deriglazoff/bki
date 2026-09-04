"""Rebuild gold set, analog catalogs, and stats from CSV exports.

Usage (from repo root):
  python complex-cases/rebuild_from_csv.py
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def typ(t: dict) -> str:
    tags = {x.strip() for x in t["tags"].split(",") if x.strip()}
    for k in ["ЗЗ", "ОЧ", "ТЧ", "Б", "ЗС"]:
        if k in tags:
            return k
    return "?"


def clean(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"\[USER=\d+\](.*?)\[/USER\]", r"\1", text)
    t = re.sub(r"\[URL=[^\]]*\](.*?)\[/URL\]", r"\1", t)
    t = re.sub(r"\[[A-Z0-9=/]+\]", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    with open(ROOT / "osparivanie-2026-tasks.csv", encoding="utf-8-sig") as f:
        tasks = {t["task_id"]: t for t in csv.DictReader(f, delimiter=";")}
    with open(ROOT / "osparivanie-2026-comments.csv", encoding="utf-8-sig") as f:
        comments = list(csv.DictReader(f, delimiter=";"))

    human = [c for c in comments if c["is_system"] == "0"]
    by_task: dict[str, list] = collections.defaultdict(list)
    for c in human:
        by_task[c["task_id"]].append(c)

    patterns = {
        "korrektno": re.compile(r"отображается корректн", re.I),
        "korrektirovka": re.compile(r"корректир|скорректир|выгрузк\w*\s+приня", re.I),
        "pko": re.compile(r"ПКО|продан|цесси", re.I),
        "prosrochka": re.compile(r"просроч", re.I),
        "zakryt": re.compile(r"договор закрыт|закрыт.*бюро|прекращен", re.I),
        "bankrot_cross": re.compile(r"банкрот", re.I),
    }
    branch_targets = {
        "korrektno": 10,
        "korrektirovka": 8,
        "pko": 6,
        "prosrochka": 6,
        "zakryt": 6,
        "bankrot_cross": 4,
    }
    priority = ["bankrot_cross", "pko", "zakryt", "korrektirovka", "prosrochka", "korrektno"]

    candidates = []
    for tid, t in tasks.items():
        if typ(t) != "ОЧ" or t["status"] != "завершена":
            continue
        msgs = sorted(by_task.get(tid, []), key=lambda m: m["date"])
        texts = [(m, clean(m["text"])) for m in msgs]
        long_texts = [(m, tx) for m, tx in texts if len(tx) >= 50]
        if not long_texts:
            continue
        joined = " ".join(tx for _, tx in texts)
        labels = [name for name, rx in patterns.items() if rx.search(joined)]
        if not labels:
            continue
        primary = next((p for p in priority if p in labels), labels[0])
        candidates.append(
            {
                "task_id": tid,
                "title": t["title"],
                "url": t["url"],
                "tags": t["tags"],
                "responsible": t["responsible"],
                "labels": labels,
                "primary": primary,
                "score": len(long_texts) + 2 * len(labels),
                "thread": [
                    {"date": m["date"], "author": m["author_name"], "text": tx}
                    for m, tx in long_texts[:8]
                ],
            }
        )
    candidates.sort(key=lambda x: -x["score"])
    selected = []
    counts: collections.Counter = collections.Counter()
    for c in candidates:
        p = c["primary"]
        if counts[p] >= branch_targets.get(p, 6) + 2 and len(selected) >= 38:
            continue
        if counts[p] >= branch_targets.get(p, 6) and len(selected) >= 30:
            if all(counts[b] >= branch_targets[b] for b in branch_targets):
                if len(selected) >= 40:
                    break
            elif counts[p] > branch_targets.get(p, 6):
                continue
        selected.append(c)
        counts[p] += 1
        if len(selected) >= 40:
            break
    for c in candidates:
        if len(selected) >= 40:
            break
        if any(s["task_id"] == c["task_id"] for s in selected):
            continue
        selected.append(c)

    gold = {
        "description": "Эталонные ОЧ-треды для регрессии правил сверки 3 бюро",
        "source": "osparivanie-2026-tasks.csv + osparivanie-2026-comments.csv",
        "count": len(selected),
        "branches": dict(collections.Counter(s["primary"] for s in selected)),
        "cases": selected,
    }
    (OUT / "och-gold-set.json").write_text(
        json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for case_type in ["ТЧ", "Б", "ЗС"]:
        items = []
        for tid, t in tasks.items():
            if typ(t) != case_type or t["status"] != "завершена":
                continue
            msgs = sorted(by_task.get(tid, []), key=lambda m: m["date"])
            texts = [clean(m["text"]) for m in msgs if len(clean(m["text"])) >= 40]
            if not texts:
                continue
            joined = " ".join(texts)
            subtype = "other"
            if case_type == "ТЧ":
                if re.search(r"паспорт", joined, re.I):
                    subtype = "passport"
                elif re.search(r"адрес", joined, re.I):
                    subtype = "address"
                elif re.search(r"ФИО|фамили", joined, re.I):
                    subtype = "fio"
                elif re.search(r"рожден", joined, re.I):
                    subtype = "birthplace"
                elif re.search(r"склейк|дву(х|мя) клиент", joined, re.I):
                    subtype = "glue_signal"
                if re.search(r"промежуточн", joined, re.I):
                    subtype = subtype + "+interim"
            elif case_type == "Б":
                if re.search(r"отображается корректн", joined, re.I):
                    subtype = "korrektno_law"
                elif re.search(r"Bankrot|банкротств.*скорректир|корректир", joined, re.I):
                    subtype = "bankrot_fix"
                elif re.search(r"ПКО|продан", joined, re.I):
                    subtype = "pko_bankrot"
            elif case_type == "ЗС":
                if re.search(r"раздел|demerge", joined, re.I):
                    subtype = "demerge"
                elif re.search(r"паспорт", joined, re.I):
                    subtype = "old_passport"
                elif re.search(r"связанн", joined, re.I):
                    subtype = "linked_task"
            items.append(
                {
                    "task_id": tid,
                    "title": t["title"],
                    "url": t["url"],
                    "tags": t["tags"],
                    "subtype": subtype,
                    "n_human_msgs": len(by_task.get(tid, [])),
                    "snippet": texts[0][:240],
                    "has_interim": bool(re.search(r"промежуточн", joined, re.I)),
                }
            )
        items.sort(key=lambda x: -x["n_human_msgs"])
        (OUT / f"analogs-{case_type}.json").write_text(
            json.dumps(
                {
                    "type": case_type,
                    "count": len(items),
                    "subtypes": dict(collections.Counter(i["subtype"] for i in items)),
                    "cases": items,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    by_type = collections.Counter(typ(t) for t in tasks.values())
    human_by: collections.Counter = collections.Counter()
    for c in human:
        t = tasks.get(c["task_id"])
        if t:
            human_by[typ(t)] += 1
    hard = by_type["ТЧ"] + by_type["Б"] + by_type["ЗС"]
    n = len(tasks)
    stats = {
        "tasks_total": n,
        "by_type": dict(by_type),
        "hard_TCH_B_ZS": hard,
        "hard_pct_flow": round(100 * hard / n, 1),
        "och_pct_flow": round(100 * by_type["ОЧ"] / n, 1),
        "human_comments_total": len(human),
        "human_by_type": dict(human_by),
        "hard_human_msgs": human_by["ТЧ"] + human_by["Б"] + human_by["ЗС"],
        "hard_pct_comments": round(
            100 * (human_by["ТЧ"] + human_by["Б"] + human_by["ЗС"]) / len(human), 1
        ),
    }
    (OUT / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"gold": gold["count"], "stats": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
