#!/usr/bin/env python3
"""
Phase 2 — Facet 추출 (Anthropic API)

입력: corpus/metadata.json (Phase 1 산출물)
      corpus/pdfs/{pmid}.pdf (있으면 full text 우선, 없으면 abstract만)
출력: outputs/facets.jsonl (한 줄당 한 facet JSON)
      outputs/facet_errors.log

환경변수 ANTHROPIC_API_KEY 필수.
모델: claude-sonnet-4-6 (비용 효율) 또는 claude-opus-4-7 (품질).
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional

# anthropic SDK (pip install anthropic)
try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Optional: PDF text extraction
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

ROOT = Path(__file__).resolve().parent.parent
META_FILE = ROOT / "corpus" / "metadata.json"
PDF_DIR = ROOT / "corpus" / "pdfs"
PROMPT_FILE = ROOT / "scripts" / "phase2_facet_prompt.md"
OUTPUT_FILE = ROOT / "outputs" / "facets.jsonl"
ERROR_LOG = ROOT / "outputs" / "facet_errors.log"

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = 2000
MAX_INPUT_CHARS = 50000  # truncate long PDFs


def extract_pdf_text(pdf_path: Path) -> str:
    if not HAS_FITZ:
        return ""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"  PDF extract failed: {e}", file=sys.stderr)
        return ""


def build_prompt_template() -> tuple[str, str]:
    """Return (system_prompt, user_template) parsed from MD file."""
    md = PROMPT_FILE.read_text()
    # Simple split on ## System and ## User
    parts = md.split("## ")
    system_prompt = ""
    user_template = ""
    for part in parts:
        if part.startswith("System\n"):
            system_prompt = part[len("System\n"):].strip()
        elif part.startswith("User\n"):
            user_template = part[len("User\n"):].strip()
    return system_prompt, user_template


def call_claude(client: Anthropic, system: str, user: str, retries: int = 3) -> Optional[str]:
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text
        except Exception as e:
            print(f"  API error (attempt {attempt + 1}/{retries}): {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    return None


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not META_FILE.exists():
        print(f"ERROR: {META_FILE} not found", file=sys.stderr)
        sys.exit(1)

    articles = json.loads(META_FILE.read_text())
    print(f"Loaded {len(articles)} articles")

    system_prompt, user_template = build_prompt_template()
    print(f"Loaded prompt template from {PROMPT_FILE}")

    client = Anthropic(api_key=api_key)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Resume: read existing facets
    done_pmids = set()
    if OUTPUT_FILE.exists():
        for line in OUTPUT_FILE.read_text().splitlines():
            try:
                done_pmids.add(json.loads(line)["pmid"])
            except Exception:
                pass
        print(f"Resuming: {len(done_pmids)} already done")

    errors = []

    with OUTPUT_FILE.open("a") as f_out:
        for i, a in enumerate(articles, 1):
            pmid = a["pmid"]
            if pmid in done_pmids:
                continue

            print(f"[{i}/{len(articles)}] {pmid}: {a['title'][:60]}")

            # Prefer PDF text if available
            pdf_path = PDF_DIR / f"{pmid}.pdf"
            if pdf_path.exists() and HAS_FITZ:
                text = extract_pdf_text(pdf_path)[:MAX_INPUT_CHARS]
                source = "pdf"
            else:
                text = a.get("abstract", "")
                source = "abstract"

            if not text or len(text) < 50:
                print(f"  ⚠ No text available, skipping")
                errors.append(f"{pmid}\tno text")
                continue

            user_msg = user_template.format(
                pmid=pmid,
                year=a.get("year", ""),
                journal=a.get("journal_iso", ""),
                title=a.get("title", ""),
                doi=a.get("doi", ""),
                abstract_or_text=text,
            )

            resp_text = call_claude(client, system_prompt, user_msg)
            if not resp_text:
                errors.append(f"{pmid}\tAPI failed after retries")
                continue

            # Parse JSON
            try:
                # Strip potential markdown code fences
                clean = resp_text.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                facet = json.loads(clean.strip())
                facet["_source"] = source
                f_out.write(json.dumps(facet, ensure_ascii=False) + "\n")
                f_out.flush()
                print(f"  ✓ facet saved")
            except Exception as e:
                print(f"  ✗ JSON parse failed: {e}")
                errors.append(f"{pmid}\tJSON parse failed: {e}\n  raw: {resp_text[:200]}")

            # Small delay
            time.sleep(0.5)

    if errors:
        ERROR_LOG.write_text("\n".join(errors))
        print(f"\n⚠ {len(errors)} errors logged to {ERROR_LOG}")

    print(f"\n✓ Facets saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
