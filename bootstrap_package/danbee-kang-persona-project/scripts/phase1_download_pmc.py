#!/usr/bin/env python3
"""
Phase 1 — PMC 오픈액세스 PDF 일괄 다운로드

입력: corpus/metadata.json (Phase 1 첫 단계 산출물)
출력: corpus/pdfs/{pmid}.pdf
      corpus/download_log.txt

PMC OAI-PMH 또는 EFetch로 OA 서브셋 PDF 다운로드.
비-OA 또는 다운로드 실패 시 manual_needed.txt에 추가 기록.
"""

import os
import sys
import json
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
META_FILE = ROOT / "corpus" / "metadata.json"
PDF_DIR = ROOT / "corpus" / "pdfs"
LOG_FILE = ROOT / "corpus" / "download_log.txt"
MANUAL_FILE = ROOT / "corpus" / "manual_needed.txt"

PMC_OA_BASE = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
EMAIL = os.environ.get("NCBI_EMAIL", "")
API_KEY = os.environ.get("NCBI_API_KEY", "")
SLEEP = 0.34 if not API_KEY else 0.11


def get_oa_pdf_url(pmcid: str) -> str | None:
    """
    Use PMC OA Web Service to get PDF URL.
    Returns None if not in OA subset.
    """
    pmcid_clean = pmcid.replace("PMC", "")
    params = {"id": f"PMC{pmcid_clean}"}
    if EMAIL:
        params["email"] = EMAIL
    if API_KEY:
        params["api_key"] = API_KEY

    try:
        r = requests.get(PMC_OA_BASE, params=params, timeout=20)
        r.raise_for_status()
        # Response is XML
        text = r.text
        # Look for <link format="pdf" href="ftp://..." />
        import re
        m = re.search(r'<link[^>]+format="pdf"[^>]+href="([^"]+)"', text)
        if m:
            url = m.group(1)
            # Convert ftp:// to https://
            url = url.replace("ftp://ftp.ncbi.nlm.nih.gov/", "https://ftp.ncbi.nlm.nih.gov/")
            return url
        return None
    except Exception as e:
        print(f"  OA lookup error for PMC{pmcid_clean}: {e}", file=sys.stderr)
        return None


def download_pdf(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  Download error: {e}", file=sys.stderr)
        return False


def main():
    if not META_FILE.exists():
        print(f"ERROR: {META_FILE} not found. Run phase1_fetch_metadata.py first.", file=sys.stderr)
        sys.exit(1)

    articles = json.loads(META_FILE.read_text())
    print(f"Loaded {len(articles)} articles from metadata.json")

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    manual_lines = []
    success = 0
    skipped = 0

    for a in articles:
        pmid = a["pmid"]
        pmcid = a.get("pmc", "")
        title_short = a["title"][:60]

        dest = PDF_DIR / f"{pmid}.pdf"
        if dest.exists():
            print(f"[SKIP] {pmid}: already downloaded")
            log_lines.append(f"SKIP\t{pmid}\talready exists")
            skipped += 1
            continue

        if not pmcid:
            print(f"[MANUAL] {pmid}: no PMC ID ({title_short})")
            manual_lines.append(f"{pmid} | DOI: {a.get('doi', 'N/A')} | {title_short}")
            log_lines.append(f"MANUAL\t{pmid}\tno PMC ID")
            continue

        print(f"[FETCH] {pmid} (PMC{pmcid.replace('PMC','')}): {title_short}")
        pdf_url = get_oa_pdf_url(pmcid)
        time.sleep(SLEEP)

        if not pdf_url:
            print(f"  → not in PMC OA subset")
            manual_lines.append(f"{pmid} | PMC{pmcid.replace('PMC','')} | not in OA subset | {title_short}")
            log_lines.append(f"NOT_OA\t{pmid}\tnot in OA subset")
            continue

        ok = download_pdf(pdf_url, dest)
        if ok:
            print(f"  ✓ saved {dest.name}")
            log_lines.append(f"OK\t{pmid}\t{dest.name}")
            success += 1
        else:
            print(f"  ✗ download failed")
            manual_lines.append(f"{pmid} | download failed | {title_short}")
            log_lines.append(f"FAIL\t{pmid}\tdownload failed")
        time.sleep(SLEEP)

    LOG_FILE.write_text("\n".join(log_lines))
    if manual_lines:
        MANUAL_FILE.write_text(
            "# 수동 다운로드 필요 논문 (institution 접속 또는 author 문의)\n"
            "# Format: PMID | identifier | reason | title\n\n" +
            "\n".join(manual_lines)
        )

    print(f"\n=== Summary ===")
    print(f"Total: {len(articles)}")
    print(f"Downloaded now: {success}")
    print(f"Already had: {skipped}")
    print(f"Manual needed: {len(manual_lines)}")
    print(f"Log: {LOG_FILE}")
    print(f"Manual list: {MANUAL_FILE}")


if __name__ == "__main__":
    main()
