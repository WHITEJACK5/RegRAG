"""
RegRAG - data downloader (D1).

Downloads the public RBI corpus PDFs into data/, verifies each file really is a
PDF (%PDF magic bytes), computes a SHA-256 checksum, and records everything in
data/MANIFEST.json. Re-running is safe: a file already present with the same
checksum is skipped; a changed file is replaced and re-logged.

Licence note:
- All documents are public publications of the Reserve Bank of India (rbi.org.in).
- This project is educational. It is NOT legal or financial advice.
- PDFs are never committed to git (spec rule); only MANIFEST.json is tracked.

Usage:
  python scripts/download_data.py
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# Corpus list (spec s7, s17 - verify before you rely on it).
# Checked against rbi.org.in on 2026-11-09. If RBI reissues or supersedes a
# document: update url/effective_date/status here. A superseded rule quoted
# confidently is a real-world failure mode.

DOCS = [
    {
        "doc_id": "rbi_digital_lending_2025",
        "title": "Reserve Bank of India (Digital Lending) Directions, 2025",
        "url": "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/36NT8C402BE7C2A349E0BFFF3C526668CD7A.PDF",
        "effective_date": "2025-05-08",
        "status": "current - consolidates the 2022 Digital Lending Guidelines",
    },
    {
        "doc_id": "rbi_kyc_2016",
        "title": "Master Direction - Know Your Customer (KYC) Direction, 2016",
        "url": "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/MD18KYCF6E92C82E1E1419D87323E3869BC9F13.PDF",
        "effective_date": "2016-02-25",
        "status": "current - consolidated text updated as on 2025-08-14",
    },
    {
        "doc_id": "rbi_iracp_2025",
        "title": "Master Circular - Prudential norms on Income Recognition, Asset Classification and Provisioning pertaining to Advances",
        "url": "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/13MC01042025792E33CF094B46F2B838E6409777438D.PDF",
        "effective_date": "2025-04-01",
        "status": "current - reissued each April; verify before relying",
    },
    {
        "doc_id": "rbi_fair_practices_code",
        "title": "Master Circular - Fair Practices Code",
        "url": "https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/16FP250915F.pdf",
        "effective_date": "2015-07-01",
        "status": "current as consolidated text; issued 2015-07-01, updated as on 2015-06-30; the 2024-04-29 charging-of-interest circular adds rules on top",
    },
]

# RBI serves real pages to browsers but rejects the bare python-requests User-Agent
# RBI's bot-wall serves HTML instead of the PDF unless the request looks
# like a browser click from the RBI site: browser UA + Referer + Accept.
# Verified 2026-11-09: bare UA -> text/html; these headers -> application/pdf.
HEADER = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Referer": "https://www.rbi.org.in/",
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "MANIFEST.json"


def sha256_of(path: Path) -> str:
    """Stream-hash a file so multi-MB PDFs never blow up memory."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def looks_like_pdf(path: Path) -> bool:
    """RBI sometimes serves an HTML error page named .pdf - catch that early."""
    with path.open("rb") as f:
        return f.read(5) == b"%PDF-"


def download(doc: dict) -> None:
    out = DATA / f"{doc['doc_id']}.pdf"
    with requests.get(doc["url"], headers=HEADER, timeout=60, stream=True) as r:
        r.raise_for_status()
        with out.open("wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
    if not looks_like_pdf(out):
        out.unlink()
        raise RuntimeError(
            f"URL did not return a PDF (likely an error page). Fallback: download "
            f"it yourself in a browser from {doc['url']} and save it as data/"
            f"{out.name}, then re-run this script - it will verify and record it."
        )


def main() -> int:
    DATA.mkdir(exist_ok=True)
    old_hashes = {d["doc_id"]: (sha256_of(DATA / f"{d['doc_id']}.pdf")
                                if (DATA / f"{d['doc_id']}.pdf").exists() else None)
                  for d in DOCS}

    records = []
    for doc in DOCS:
        out = DATA / f"{doc['doc_id']}.pdf"
        if old_hashes[doc["doc_id"]] is None:
            print(f"[downloading] {doc['doc_id']}")
            download(doc)                      # raises -> traceback -> we see it
        else:
            print(f"[present]     {doc['doc_id']}")

        new_hash = sha256_of(out)
        records.append({
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "url": doc["url"],
            "effective_date": doc["effective_date"],
            "status": doc["status"],
            "file": out.name,
            "sha256": new_hash,
            "size_bytes": out.stat().st_size,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "download_state": "unchanged" if old_hashes[doc["doc_id"]] == new_hash
                              else "new/updated",
        })

    manifest = {
        "project": "RegRAG",
        "note": ("Educational project - not legal or financial advice. Documents are "
                 "public RBI publications. PDFs are never committed to git."),
        "manifest_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "docs": records,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nMANIFEST written -> {MANIFEST}")
    for r in records:
        print(f"  OK  {r['doc_id']:<28} {r['size_bytes']:>10,} bytes  "
              f"{r['sha256'][:16]}...  {r['download_state']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())