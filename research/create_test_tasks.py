#!/usr/bin/env python3
"""Create Bitrix test tasks from task-pdfs folders, mirroring task 494473."""

from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PDF_ROOT = ROOT / "task-pdfs"
FOLDER_IDS = ["436602", "436603", "436604", "436605", "436598", "436599", "436600", "436601"]
GROUP_ID = 437
RESPONSIBLE_ID = 43357
DEADLINE = "2026-09-09T18:00:00+03:00"
STAGE_ID = 12144
DISK_ROOT = 716119

CLASSIFICATION = {
    "436598": (
        "[B]Классификация[/B] (по classification.md, ishod.txt / vhod.txt целиком)\n\n"
        "[B]Смешанный пакет[/B]\n"
        "[B]Теги:[/B] ОЧ, ТЧ, Б\n\n"
        "[B]ОЧ[/B] — исх. НБКИ № 242253, адресат АО МФК «САММИТ»:\n"
        "• УИД ca74e51b-18cc-11d8-8d1e-4989204ab1a0-1 — Просрочка, Закрытие договора "
        "(обнулить продолжительность просрочки; договор закрыт)\n"
        "• УИД d0e1a7ef-8550-11d8-801f-4cf4cb65b886-f — Просрочка, Сумма/платёж, Продажа/ПКО "
        "(переуступлен; обнулить просрочку, платежи за 24 мес., СМП; «Несвоевременно» → «Своевременно»)\n\n"
        "[B]ТЧ[/B] — шапка заявления ВХ 277644:\n"
        "• Паспорт — дата выдачи ранее выданного: 17.02.2009, не 19.02.2009 (серия 3608 № 920735)\n"
        "• Телефон — оставить +7(939)7127000; удалить +7(961)3844607 и +79032570270 (рабочие)\n\n"
        "[B]Б[/B] — определение АС Самарской области от 24.06.2025, дело № А55-33884/2022 "
        "(реализация имущества завершена; предыдущее ФИО Арапова Т.П.):\n"
        "• Дата признания — 24.06.2025\n"
        "• Просрочка после банкротства — удалить просрочки после 24.06.2025\n"
        "• Статус в БКИ / прекращение процедуры — ДФПО 24.06.2025, основание «банкротство»\n"
        "• Банкротство + ПКО — УИД d0e1a7ef-…-f переуступлен"
    ),
    "436599": (
        "[B]Классификация[/B] (по classification.md, ishod.txt / vhod.txt целиком)\n\n"
        "[B]Смешанный пакет[/B]\n"
        "[B]Теги:[/B] ТЧ, ЗЗ\n\n"
        "[B]ТЧ[/B] — исх. Скоринг Бюро OFL_20251230 (адресат АО МФК «Саммит») + шапка заявления:\n"
        "• Адрес — оставить 127540, ул. Дубнинская, д. 12, к. 1, кв. 280; удалить иные адреса регистрации\n"
        "• Паспорт — 4518 № 667189, выдан 27.06.2018, ГУ МВД России по г. Москве, к/п 770-016\n"
        "• ФИО / дата рождения — Соложенцев Алексей Юрьевич, 15.06.1973, г. Москва\n\n"
        "[B]ЗЗ[/B] — заявление (claim):\n"
        "• Заявка — удалить заявки, которые субъект не подавал (приложение 1), в т.ч. УИД "
        "1be56be0-d3e4-11e9-86ee-5820b18309a8-1 от 25.11.2020 АО КБ «Пойдём!»\n"
        "• Удаление запросов КИ — удалить неинициированные запросы (приложение 2)\n"
        "В исх. кредиты адресата не названы → контур ОЧ этому источнику не ставим"
    ),
    "436600": (
        "[B]Классификация[/B] (по classification.md, ishod.txt целиком; входящего файла нет)\n\n"
        "[B]ЗЗ[/B]\n"
        "[B]Теги:[/B] ЗЗ\n\n"
        "Исх. ОКБ № 210315/НДО от 30.12.2025, адресат САММИТ ООО МФК:\n"
        "• Заявка / мошенничество — субъект Шишов Дмитрий Федорович (16.11.1988, паспорт 4608 470753) "
        "оспаривает заявку от 25.09.2025, УИД ba306608-2e3a-11dc-8e4b-a02417a591e2-3: «Заявку на кредит не оформлял»"
    ),
    "436601": (
        "[B]Классификация[/B] (по classification.md, ishod.txt целиком; входящего файла нет)\n\n"
        "[B]ЗЗ[/B]\n"
        "[B]Теги:[/B] ЗЗ\n\n"
        "Исх. ОКБ № 210632/НДО от 30.12.2025, адресат ООО МКК «ДЗБР»:\n"
        "• Заявка / мошенничество — субъект Овчинников Алексей Федорович (25.02.1960, паспорт 4508 135881) "
        "оспаривает заявку от 24.09.2025, УИД 7b83b8fc-2dd9-11dc-8b61-6139f662af42-a: «Заявку на кредит не оформлял»"
    ),
    "436602": (
        "[B]Классификация[/B] (по classification.md, ishod.txt целиком; входящего файла нет)\n\n"
        "[B]ЗЗ[/B]\n"
        "[B]Теги:[/B] ЗЗ\n\n"
        "Исх. ОКБ № 210329/НДО от 30.12.2025, адресат ООО МКК «ДЗБР»:\n"
        "• Заявка / мошенничество — субъект Зайцев Юрий Николаевич (08.02.1965, паспорт 4608 566278) "
        "оспаривает заявку от 19.11.2025, УИД a9cc3546-59df-11dc-926d-51187786571e-1: «Заявку на кредит не оформлял»"
    ),
    "436603": (
        "[B]Классификация[/B] (по classification.md, ishod.txt целиком; входящего файла нет)\n\n"
        "[B]ЗЗ[/B]\n"
        "[B]Теги:[/B] ЗЗ\n\n"
        "Исх. ОКБ № 210645/НДО от 30.12.2025, адресат САММИТ ООО МФК:\n"
        "• Заявка / мошенничество — субъект Золин Олег Викторович (24.09.1971, паспорт 4616 316727) "
        "оспаривает заявки от 27.11.2025, УИД 0b19907f-6015-11dc-8e5c-5063b3dfd506-3 и "
        "cb241475-5f81-11dc-976e-eb7ee388f82c-6: «Заявку на кредит не оформлял»"
    ),
    "436604": (
        "[B]Классификация[/B] (по classification.md, ishod.txt / vhod.txt целиком)\n\n"
        "[B]Смешанный пакет[/B]\n"
        "[B]Теги:[/B] ЗЗ, ТЧ\n\n"
        "[B]ЗЗ[/B] — исх. НБКИ № 242767, адресат АО МФК «САММИТ»:\n"
        "• Удаление запросов КИ — запросы 27.03.2018 и 26.07.2018 (подтвердить согласие либо удалить). "
        "Во ВХ те же даты есть у АО МФК «САММИТ» в списке запросов без согласия\n\n"
        "[B]ТЧ[/B] — заявление ВХ 277436:\n"
        "• ФИО / дата рождения / место рождения — Алипкачева Нурият Абдулмажидовна, 24.03.1987, "
        "с. Манаскент Ленинского р-на республики Дагестан; ошибка в ФИО, дате и месте рождения\n"
        "• Паспорт — 82 07 337749, выдан 12.09.2007, к/п 050-004\n\n"
        "Пункты ВХ про закрытие счетов (ДЗП-Центр, ПКО Юнона и др.) — чужие УИД, контур ОЧ этому источнику не дают"
    ),
    "436605": (
        "[B]Классификация[/B] (по classification.md, ishod.txt / vhod.txt целиком)\n\n"
        "[B]Смешанный пакет[/B]\n"
        "[B]Теги:[/B] ОЧ, ТЧ, ЗЗ\n\n"
        "[B]ОЧ[/B] — исх. НБКИ № 242959 (АО МФК «САММИТ») и № 242980 (ООО ПКО «Доброзайм»):\n"
        "• УИД 4c2f6783-6ba0-11d9-9752-418d643b662f-1 — Просрочка, Продажа/ПКО "
        "(во ВХ: просрочка май–сентябрь 2023 у Саммит; июнь 2023 – февраль 2024 у ПКО «Доброзайм»; "
        "субъект пишет, что обязательства исполнены в срок)\n"
        "• УИД 61b53148-f05b-11d8-96c8-6abe6dc555b6-4 — в исх. Саммит как заявка от 17.10.2022, "
        "во ВХ тоже в списке заявок; подтип ОЧ по этому УИД из ВХ не заполнен\n\n"
        "[B]ТЧ[/B] — форма ОСП-1ФИЗ:\n"
        "• ФИО — «Сахибгареева Лилия Эривовна» → «Сахибгареева Лилия Эриковна»\n"
        "• Паспорт — 80 12 692517, выдан 11.11.2013; ранее 8005 455597 (13.06.2006) и 8011 535442 (18.07.2012)\n\n"
        "[B]ЗЗ[/B] — исх. Саммит (заявки/запросы 04.11.2022, 03.07.2023) + весь ВХ: "
        "удалить заявки, которые субъект не подавала, в т.ч. Саммит 10.04.2023 / 4c2f6783-…-1 и 17.10.2022 / 61b53148-…-4"
    ),
}

TITLES = {
    "436598": "ТЕСТ 436598 Моисеева Т.П.",
    "436599": "ТЕСТ 436599 Соложенцев А.Ю.",
    "436600": "ТЕСТ 436600 Шишов Д.Ф.",
    "436601": "ТЕСТ 436601 Овчинников А.Ф.",
    "436602": "ТЕСТ 436602 Зайцев Ю.Н.",
    "436603": "ТЕСТ 436603 Золин О.В.",
    "436604": "ТЕСТ 436604 Алипкачева Н.А.",
    "436605": "ТЕСТ 436605 Сахибгареева Л.Э.",
}


def load_webhook() -> str:
    env_url = __import__("os").environ.get("B24_DEFAULT_WEBHOOK")
    if env_url:
        return env_url.rstrip("/") + "/"
    mcp = Path.home() / ".cursor" / "mcp.json"
    data = json.loads(mcp.read_text(encoding="utf-8"))
    return data["mcpServers"]["bitrix24"]["env"]["B24_DEFAULT_WEBHOOK"].rstrip("/") + "/"


def call(session: requests.Session, webhook: str, method: str, payload: dict, timeout: int = 180) -> dict:
    last = None
    for attempt in range(5):
        try:
            resp = session.post(webhook + method, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(f"{data.get('error')}: {data.get('error_description')}")
            return data
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{method} failed: {last}")


def is_incoming(name: str) -> bool:
    lower = name.lower()
    return lower.startswith("вх") or lower.startswith("claim") or lower.startswith("bx")


def is_outgoing(name: str) -> bool:
    lower = name.lower()
    return (
        lower.startswith("исх")
        or lower.startswith("запрос")
        or lower.startswith("correction")
    )


def collect_files(folder: Path) -> tuple[list[Path], str | None, str | None]:
    pdfs: list[Path] = []
    seen_sizes: set[int] = set()
    vhod_parts: list[str] = []
    ishod_parts: list[str] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() == ".pdf":
            if " (1)." in path.name:
                continue
            size = path.stat().st_size
            if size in seen_sizes:
                continue
            seen_sizes.add(size)
            pdfs.append(path)
        elif path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8")
            header = f"===== {path.stem} =====\n"
            if is_incoming(path.name):
                vhod_parts.append(header + text)
            elif is_outgoing(path.name):
                ishod_parts.append(header + text)
    vhod = "\n\n".join(vhod_parts) if vhod_parts else None
    ishod = "\n\n".join(ishod_parts) if ishod_parts else None
    return pdfs, ishod, vhod


def upload_file(session: requests.Session, webhook: str, folder_id: int, name: str, content: bytes) -> int:
    payload = {
        "id": folder_id,
        "data": {"NAME": name},
        "fileContent": base64.b64encode(content).decode("ascii"),
        "generateUniqueName": True,
    }
    data = call(session, webhook, "disk.folder.uploadfile", payload, timeout=300)
    result = data.get("result") or {}
    object_id = result.get("ID") or result.get("id")
    if not object_id:
        raise RuntimeError(f"upload {name}: no ID in {result!r}"[:400])
    return int(object_id)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    webhook = load_webhook()
    session = requests.Session()
    created_folder = call(
        session,
        webhook,
        "disk.folder.addsubfolder",
        {"id": DISK_ROOT, "data": {"NAME": f"ТЕСТ оспаривание {time.strftime('%Y-%m-%d %H-%M')}"}},
    )
    folder_id = int((created_folder.get("result") or {}).get("ID"))
    print(f"disk folder {folder_id}", flush=True)

    created: list[tuple[str, str]] = []
    for src_id in FOLDER_IDS:
        src = PDF_ROOT / src_id
        pdfs, ishod, vhod = collect_files(src)
        disk_ids: list[int] = []
        for pdf in pdfs:
            print(f"{src_id} upload pdf {pdf.name} ({pdf.stat().st_size})", flush=True)
            disk_ids.append(upload_file(session, webhook, folder_id, pdf.name, pdf.read_bytes()))
        if ishod:
            print(f"{src_id} upload ishod.txt", flush=True)
            disk_ids.append(upload_file(session, webhook, folder_id, "ishod.txt", ishod.encode("utf-8")))
        if vhod:
            print(f"{src_id} upload vhod.txt", flush=True)
            disk_ids.append(upload_file(session, webhook, folder_id, "vhod.txt", vhod.encode("utf-8")))
        fields = {
            "TITLE": TITLES[src_id],
            "DESCRIPTION": "",
            "RESPONSIBLE_ID": RESPONSIBLE_ID,
            "CREATED_BY": RESPONSIBLE_ID,
            "GROUP_ID": GROUP_ID,
            "DEADLINE": DEADLINE,
            "STAGE_ID": STAGE_ID,
            "PRIORITY": 1,
            "UF_TASK_WEBDAV_FILES": [f"n{oid}" for oid in disk_ids],
        }
        added = call(session, webhook, "tasks.task.add", {"fields": fields})
        task = (added.get("result") or {}).get("task") or added.get("result") or {}
        task_id = str(task.get("id") or task.get("ID") or "")
        if not task_id:
            raise RuntimeError(f"no task id: {added!r}"[:500])
        url = f"https://resultforyou.ru/workgroups/group/437/tasks/task/view/{task_id}/"
        print(f"{src_id} -> {task_id} {url}", flush=True)
        comment = CLASSIFICATION[src_id]
        call(
            session,
            webhook,
            "task.commentitem.add",
            {"TASK_ID": int(task_id), "FIELDS": {"POST_MESSAGE": comment, "AUTHOR_ID": RESPONSIBLE_ID}},
        )
        created.append((src_id, url))
        time.sleep(0.3)

    print("=== created ===", flush=True)
    for src_id, url in created:
        print(f"{src_id}\t{url}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
