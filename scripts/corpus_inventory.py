"""RegRAG corpus inventory (D2).

Prints what the corpus actually contains right now:
- every document recorded in data/MANIFEST.json (checksum, size, dates, status)
- the synthetic policy's size, label and trace coverage

Run before each parsing day (D3+) as a sanity check:
  python scripts/corpus_inventory.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "MANIFEST.json"
POLICY = DATA / "synthetic_policy_v1.md"

TRACE_DOCS = [
    "rbi_kyc_2016",
    "rbi_digital_lending_2025",
    "rbi_iracp_2025",
    "rbi_fair_practices_code",
]


def main() -> int:
    if not MANIFEST.exists():
        print("MANIFEST.json missing - run scripts/download_data.py first")
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print(f"Corpus inventory - {len(manifest['docs'])} documents from MANIFEST\n")
    for d in manifest["docs"]:
        exists = (DATA / d["file"]).exists()
        flag = "OK     " if exists else "MISSING"
        print(f"[{flag}] {d['doc_id']}")
        print(f"       file            {d['file']}  ({d['size_bytes']:,} bytes)")
        print(f"       sha256          {d['sha256'][:16]}...")
        print(f"       effective_date  {d['effective_date']}")
        print(f"       status          {d['status']}")
        print()

    if POLICY.exists():
        text = POLICY.read_text(encoding="utf-8")
        words = len(text.split())
        labelled = "SYNTHETIC" in text[:2000]
        verify_flags = len(re.findall("VERIFY-D3", text))
        traces = [doc for doc in TRACE_DOCS if doc in text]
        print("Synthetic policy - data/synthetic_policy_v1.md")
        print(f"       words           {words:,}")
        print(f"       labelled        {'yes' if labelled else 'NO - FIX'}")
        print(f"       VERIFY-D3 flags {verify_flags} (informational)")
        print(f"       traces          {len(traces)}/4 -> {', '.join(traces)}")
    else:
        print("Synthetic policy missing (expected data/synthetic_policy_v1.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
