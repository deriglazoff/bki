#!/usr/bin/env python3
"""Extract text from task PDFs: native text when present, Tesseract OCR otherwise."""

from __future__ import annotations

import csv
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PDF_ROOT = ROOT / "task-pdfs"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_DIR = str(ROOT / ".tessdata")
LANG = "rus+eng"
DPI = 200
MIN_NATIVE_CHARS = 80
WORKERS = 6
MANIFEST = PDF_ROOT / "ocr_manifest.csv"
LOG = PDF_ROOT / "ocr.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def txt_path_for(pdf: Path) -> Path:
    return pdf.with_suffix(".txt")


def native_page_text(page) -> str:
    return (page.get_text("text") or "").strip()


def ocr_page(page) -> str:
    pix = page.get_pixmap(dpi=DPI, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    pix = None
    text = pytesseract.image_to_string(
        img,
        lang=LANG,
        config=f"--tessdata-dir {TESSDATA_DIR} --psm 6",
        timeout=90,
    )
    return (text or "").strip()


def process_pdf(pdf_str: str) -> dict:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    pdf = Path(pdf_str)
    dest = txt_path_for(pdf)
    result = {
        "pdf": str(pdf.relative_to(PDF_ROOT)),
        "txt": str(dest.relative_to(PDF_ROOT)),
        "pages": 0,
        "ocr_pages": 0,
        "native_pages": 0,
        "chars": 0,
        "status": "ok",
        "error": "",
        "seconds": 0.0,
    }
    t0 = time.time()
    try:
        if dest.exists() and dest.stat().st_size > 40:
            result["status"] = "skipped_exists"
            result["chars"] = dest.stat().st_size
            result["seconds"] = round(time.time() - t0, 2)
            return result
        doc = pymupdf.open(pdf)
        parts: list[str] = []
        for i, page in enumerate(doc, start=1):
            result["pages"] += 1
            native = native_page_text(page)
            if len(native) >= MIN_NATIVE_CHARS:
                body = native
                result["native_pages"] += 1
            else:
                ocr = ocr_page(page)
                if len(ocr) >= len(native):
                    body = ocr
                    result["ocr_pages"] += 1
                else:
                    body = native
                    result["native_pages"] += 1
            parts.append(f"===== стр. {i} =====\n{body}")
        doc.close()
        text = "\n\n".join(parts).strip() + "\n"
        dest.write_text(text, encoding="utf-8")
        result["chars"] = len(text)
        result["status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(exc)[:400]
    result["seconds"] = round(time.time() - t0, 2)
    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    pdfs = sorted(PDF_ROOT.rglob("*.pdf"))
    log(f"pdfs: {len(pdfs)} workers={WORKERS}")
    rows: list[dict] = []
    done = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(process_pdf, str(p)): p for p in pdfs}
        for fut in as_completed(futs):
            row = fut.result()
            rows.append(row)
            done += 1
            if done % 25 == 0 or done == len(pdfs):
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(pdfs) - done) / rate if rate else 0
                log(
                    f"{done}/{len(pdfs)} last={row['pdf'][:70]} "
                    f"status={row['status']} ocr={row['ocr_pages']} "
                    f"eta_min={eta/60:.1f}"
                )
    fieldnames = ["pdf", "txt", "pages", "ocr_pages", "native_pages", "chars", "status", "seconds", "error"]
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in sorted(rows, key=lambda r: r["pdf"]):
            writer.writerow(row)
    from collections import Counter

    counts = Counter(r["status"] for r in rows)
    ocr_pages = sum(r["ocr_pages"] for r in rows)
    native_pages = sum(r["native_pages"] for r in rows)
    log("=== summary ===")
    log(f"files: {len(rows)}")
    log(f"status: {dict(counts)}")
    log(f"native_pages: {native_pages} ocr_pages: {ocr_pages}")
    log(f"manifest: {MANIFEST}")
    log(f"elapsed_min: {(time.time()-t0)/60:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
