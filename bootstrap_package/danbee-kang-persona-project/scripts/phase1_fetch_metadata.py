#!/usr/bin/env python3
"""
Phase 1 — PubMed 메타데이터 일괄 수집

입력: data/pmids_to_fetch.txt (46 PMID)
출력: corpus/metadata.json (전체 메타데이터)
      corpus/metadata_summary.csv (요약 표)

NCBI E-utilities API 사용. Rate limit 준수 (3 req/sec without key).
환경변수 NCBI_EMAIL 설정 권장 (NCBI etiquette).
NCBI_API_KEY 있으면 10 req/sec 가능.
"""

import os
import sys
import json
import time
import csv
from pathlib import Path
from typing import Optional

import requests
from xml.etree import ElementTree as ET

# 프로젝트 루트 추정
ROOT = Path(__file__).resolve().parent.parent
PMID_FILE = ROOT / "data" / "pmids_to_fetch.txt"
OUTPUT_JSON = ROOT / "corpus" / "metadata.json"
OUTPUT_CSV = ROOT / "corpus" / "metadata_summary.csv"

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = os.environ.get("NCBI_EMAIL", "")
API_KEY = os.environ.get("NCBI_API_KEY", "")

# Rate limit (sec between requests)
SLEEP = 0.34 if not API_KEY else 0.11


def fetch_pubmed_xml(pmids: list[str]) -> str:
    """Fetch XML from PubMed efetch endpoint. Batch up to 200 PMIDs."""
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    if EMAIL:
        params["email"] = EMAIL
    if API_KEY:
        params["api_key"] = API_KEY

    r = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.text


def parse_article(article_elem) -> dict:
    """Parse one PubmedArticle XML element to dict."""
    def text_of(elem, path):
        node = elem.find(path)
        return node.text if node is not None and node.text else ""

    pmid = text_of(article_elem, ".//PMID")
    title = text_of(article_elem, ".//ArticleTitle")
    journal = text_of(article_elem, ".//Journal/Title")
    journal_iso = text_of(article_elem, ".//Journal/ISOAbbreviation")

    # Year
    year = text_of(article_elem, ".//PubDate/Year")
    if not year:
        # MedlineDate fallback
        year = text_of(article_elem, ".//PubDate/MedlineDate")[:4]

    # Abstract (multiple AbstractText elements may exist with labels)
    abstract_parts = []
    for at in article_elem.findall(".//Abstract/AbstractText"):
        label = at.get("Label", "")
        text = at.text or ""
        if label:
            abstract_parts.append(f"{label}: {text}")
        else:
            abstract_parts.append(text)
    abstract = "\n".join(abstract_parts)

    # Authors with affiliations
    authors = []
    for au in article_elem.findall(".//AuthorList/Author"):
        last = text_of(au, "LastName")
        fore = text_of(au, "ForeName")
        affs = [a.text for a in au.findall(".//AffiliationInfo/Affiliation") if a.text]
        authors.append({
            "last_name": last,
            "fore_name": fore,
            "affiliations": affs,
        })

    # Identifiers (DOI, PMC)
    doi = ""
    pmc = ""
    for id_elem in article_elem.findall(".//ArticleIdList/ArticleId"):
        id_type = id_elem.get("IdType", "")
        if id_type == "doi":
            doi = id_elem.text or ""
        elif id_type == "pmc":
            pmc = id_elem.text or ""

    # Keywords
    keywords = [k.text for k in article_elem.findall(".//KeywordList/Keyword") if k.text]

    # MeSH terms
    mesh = [m.text for m in article_elem.findall(".//MeshHeading/DescriptorName") if m.text]

    # Article types
    pub_types = [pt.text for pt in article_elem.findall(".//PublicationTypeList/PublicationType") if pt.text]

    return {
        "pmid": pmid,
        "year": year,
        "title": title,
        "journal": journal,
        "journal_iso": journal_iso,
        "abstract": abstract,
        "authors": authors,
        "doi": doi,
        "pmc": pmc,
        "keywords": keywords,
        "mesh_terms": mesh,
        "publication_types": pub_types,
    }


def main():
    if not PMID_FILE.exists():
        print(f"ERROR: {PMID_FILE} not found", file=sys.stderr)
        sys.exit(1)

    pmids = [line.strip() for line in PMID_FILE.read_text().splitlines() if line.strip()]
    print(f"Loaded {len(pmids)} PMIDs from {PMID_FILE}")

    if not EMAIL:
        print("WARNING: NCBI_EMAIL not set. Set it for API etiquette.")

    # Batch in chunks of 200 (NCBI limit)
    all_articles = []
    chunk_size = 100  # conservative
    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i:i + chunk_size]
        print(f"Fetching chunk {i // chunk_size + 1} ({len(chunk)} PMIDs)...")
        xml_text = fetch_pubmed_xml(chunk)
        root = ET.fromstring(xml_text)
        for article in root.findall(".//PubmedArticle"):
            parsed = parse_article(article)
            all_articles.append(parsed)
        time.sleep(SLEEP)

    # Sort by year desc
    all_articles.sort(key=lambda a: a.get("year", ""), reverse=True)

    # Save full JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(all_articles, indent=2, ensure_ascii=False))
    print(f"✓ Full metadata saved: {OUTPUT_JSON} ({len(all_articles)} articles)")

    # Summary CSV
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["PMID", "Year", "Journal_ISO", "Title", "DOI", "PMC", "Author_Position",
                         "Has_Abstract", "Num_Authors"])
        for a in all_articles:
            # Find Danbee Kang author position
            position = ""
            for idx, au in enumerate(a["authors"], 1):
                if au["last_name"] == "Kang" and au["fore_name"] == "Danbee":
                    if idx == 1:
                        position = "first"
                    elif idx == len(a["authors"]):
                        position = "last"
                    else:
                        position = f"middle ({idx}/{len(a['authors'])})"
                    break
            writer.writerow([
                a["pmid"], a["year"], a["journal_iso"], a["title"], a["doi"],
                a.get("pmc", ""), position, bool(a["abstract"]), len(a["authors"]),
            ])
    print(f"✓ Summary CSV saved: {OUTPUT_CSV}")

    # PMC subset (for download)
    pmc_pmids = [a["pmid"] for a in all_articles if a.get("pmc")]
    pmc_list = ROOT / "corpus" / "pmc_available_pmids.txt"
    pmc_list.write_text("\n".join(pmc_pmids))
    print(f"✓ PMC-available PMIDs: {len(pmc_pmids)} (saved to {pmc_list})")

    # Manual needed
    no_pmc = [a["pmid"] for a in all_articles if not a.get("pmc")]
    manual_list = ROOT / "corpus" / "manual_needed.txt"
    manual_list.write_text(
        "# 비-PMC 논문 (institution 접속으로 수동 다운로드 필요)\n"
        "# Format: PMID | DOI | Title\n\n" +
        "\n".join(
            f"{a['pmid']} | https://doi.org/{a['doi']} | {a['title'][:80]}"
            for a in all_articles if not a.get("pmc")
        )
    )
    print(f"✓ Non-PMC list: {len(no_pmc)} articles (saved to {manual_list})")


if __name__ == "__main__":
    main()
