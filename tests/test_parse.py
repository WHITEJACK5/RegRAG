"""D3 parser tests: the invariants we audit by eye, enforced by code.

These tests read the parsed files with explicit UTF-8 encoding, so they see
the bytes on disk — not whatever codec the PowerShell console picks.
"""
import json
import re
from pathlib import Path

PARSED = Path(__file__).resolve().parent.parent / "data" / "parsed"
REQUIRED_KEYS = {"block_id", "doc_id", "page", "section_top", "section",
                 "text", "is_table", "effective_date"}


def _blocks():
    for f in sorted(PARSED.glob("*_blocks.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            yield f.name, json.loads(line)


def test_every_block_has_full_schema():
    for name, b in _blocks():
        assert REQUIRED_KEYS <= set(b), f"{name}: {b.get('block_id')} missing keys"


def test_no_mojibake_signature_in_any_block():
    # 'â€' is the cp1252-mis-decode signature (as in â€˜ â€™ â€“ â€œ)
    bad = [(name, b["block_id"]) for name, b in _blocks()
           if "â€" in b["text"]]
    assert not bad, f"mojibake found: {bad[:5]}"


def test_effective_date_matches_manifest():
    manifest = json.loads(
        (PARSED.parent / "MANIFEST.json").read_text(encoding="utf-8"))
    dates = {d["doc_id"]: d["effective_date"] for d in manifest["docs"]}
    for name, b in _blocks():
        assert b["effective_date"] == dates[b["doc_id"]]


def test_no_dotted_leader_toc_survives_in_text_blocks():
    for name, b in _blocks():
        if b["is_table"]:
            continue
        assert not re.search(r"\.{5,}", b["text"]), \
            f"{name}: TOC dotted leaders survived in {b['block_id']}"