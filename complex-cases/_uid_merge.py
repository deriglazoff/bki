# Merge page-NNNN.json files into uid-raw-descriptions.json + uid-raw-ids.txt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "_uid-pages"
OUT = ROOT / "uid-raw-descriptions.json"
IDS = ROOT / "uid-raw-ids.txt"

PAGES.mkdir(exist_ok=True)

by_id = {}
for p in sorted(PAGES.glob("page-*.json")):
    data = json.loads(p.read_text(encoding="utf-8"))
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    for t in tasks:
        tid = str(t.get("id") or t.get("ID") or "")
        if not tid:
            continue
        by_id[tid] = {
            "id": tid,
            "title": t.get("title") or t.get("TITLE") or "",
            "description": t.get("description") or t.get("DESCRIPTION") or "",
        }

items = sorted(by_id.values(), key=lambda x: int(x["id"]))
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
IDS.write_text("\n".join(t["id"] for t in items) + ("\n" if items else ""), encoding="utf-8")
print(f"unique={len(items)} min={items[0]['id'] if items else '-'} max={items[-1]['id'] if items else '-'} pages={len(list(PAGES.glob('page-*.json')))}")
