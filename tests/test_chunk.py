"""D6 chunker contract tests: corpus invariants + unit tests on crafted blocks."""
import json
from pathlib import Path

import pytest

from regrag.ingest.chunk import (MAX_TOKENS, MIN_TOKENS, OVERLAP_TOKENS,
                                 chunk_doc, blocks_from_markdown, count_tokens)
ROOT = Path(__file__).resolve().parents[1]
CHUNK_DIR = ROOT / "data" / "chunks"
PARSED = ROOT / "data" / "parsed"
SYNTH = ROOT / "data" / "synthetic_policy_v1.md"

REQUIRED = {"chunk_id", "doc_id", "section", "pages", "is_table",
            "effective_date", "block_ids", "text"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def all_chunks() -> list[dict]:
    rows = []
    for f in sorted(CHUNK_DIR.glob("*_chunks.jsonl")):
        rows += load_jsonl(f)
    return rows


def all_blocks() -> list[dict]:
    rows = []
    for f in sorted(PARSED.glob("*_blocks.jsonl")):
        rows += load_jsonl(f)
    return rows


def mk(bid: str, text: str, section: str = "S", is_table: bool = False,
       page: int = 1, eff: str = "2026-01-01") -> dict:
    return {"block_id": bid, "doc_id": "t", "page": page, "section": section,
            "text": text, "is_table": is_table, "effective_date": eff}


def filler(n: int, seed: str = "w") -> str:
    return " ".join(f"{seed}{i}" for i in range(n))


# ---------- corpus-level invariants ----------

def test_every_chunk_has_full_schema():
    for c in all_chunks():
        assert REQUIRED <= set(c), c["chunk_id"]
        assert c["text"].strip()
        assert c["block_ids"]
        assert c["pages"] and all(isinstance(p, int) for p in c["pages"])


def test_chunk_ids_unique_and_prefixed():
    chunks = all_chunks()
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
    for c in chunks:
        assert c["chunk_id"].startswith(c["doc_id"] + "_c")


def test_no_text_chunk_under_100_tokens():
    for c in all_chunks():
        assert count_tokens(c["text"]) >= MIN_TOKENS, c["chunk_id"]


def test_no_prose_chunk_far_over_500_tokens():
    # Documented tail-absorb seam: a sub-MIN chunk may absorb one final
    # piece, worst case (MIN-1) + PIECE_MAX < MAX + MIN tokens.
    for c in all_chunks():
        if not c["is_table"]:
            assert count_tokens(c["text"]) <= MAX_TOKENS + MIN_TOKENS, c["chunk_id"]


def test_every_block_is_covered_with_no_phantoms():
    blocks = all_blocks() + blocks_from_markdown(SYNTH, "synthetic_policy_v1")
    expected = {b["block_id"] for b in blocks}
    covered = [bid for c in all_chunks() for bid in c["block_ids"]]
    assert set(covered) == expected, "lost or phantom block_ids"
    assert len(covered) >= len(expected)


def test_tables_are_never_split():
    for b in all_blocks() + blocks_from_markdown(SYNTH, "synthetic_policy_v1"):
        if b["is_table"]:
            hit = any(b["text"] in c["text"] and c["doc_id"] == b["doc_id"]
                      for c in all_chunks())
            assert hit, f"table {b['block_id']} not found whole in any chunk"


def test_effective_date_is_inherited_not_invented():
    by_doc = {}
    for b in all_blocks():
        by_doc.setdefault(b["doc_id"], set()).add(b["effective_date"])
    for c in all_chunks():
        if c["doc_id"] in by_doc:
            assert c["effective_date"] in by_doc[c["doc_id"]], c["chunk_id"]


def test_chunking_is_deterministic():
    blocks = load_jsonl(PARSED / "rbi_iracp_2025_blocks.jsonl")
    assert chunk_doc("rbi_iracp_2025", blocks) == \
        load_jsonl(CHUNK_DIR / "rbi_iracp_2025_chunks.jsonl")


# ---------- unit tests on crafted blocks ----------

def test_orphan_tail_merges_backward():
    """Regression for the 16 Nov crash: final chunk < MIN must merge,
    carrying its block_ids, into the previous chunk."""
    chunks = chunk_doc("t", [mk("b1", filler(150, "A")),
                             mk("b2", filler(50, "B"), section="T")])
    assert len(chunks) == 1
    assert chunks[0]["block_ids"] == ["b1", "b2"]


def test_numbered_clauses_are_never_split():
    clauses, sentinels = [], []
    for r in ["i", "ii", "iii", "iv", "v"]:
        s = f"SENT-{r}-START"
        sentinels.append(s)
        clauses.append(f"({r}) {s} " + filler(110, r))
    chunks = chunk_doc("t", [mk("b1", "Intro. " + " ".join(clauses))])
    prose = [c["text"] for c in chunks if not c["is_table"]]
    for r, s in zip(["i", "ii", "iii", "iv", "v"], sentinels):
        head = f"({r}) {s} {r}0 {r}1 {r}2 {r}3 {r}4"  # first words of the clause
        assert any(head in t for t in prose), f"clause ({r}) split across chunks"


def test_split_pieces_carry_overlap():
    body = " ".join(f"({r}) {filler(130, r)}" for r in ["i", "ii", "iii", "iv"])
    chunks = [c for c in chunk_doc("t", [mk("b1", body)]) if not c["is_table"]]
    assert len(chunks) >= 2
    for prev, nxt in zip(chunks, chunks[1:]):
        shared = nxt["text"].split()[:30]
        assert shared == prev["text"].split()[-OVERLAP_TOKENS:-OVERLAP_TOKENS + 30], \
            "no 15% overlap between pieces"


def test_sections_never_mix_when_both_are_big():
    chunks = chunk_doc("t", [mk("b1", filler(200, "X"), section="X"),
                             mk("b2", filler(200, "Y"), section="Y")])
    assert len(chunks) == 2
    assert {c["section"] for c in chunks} == {"X", "Y"}
    assert all("Y0" not in c["text"] or "X0" not in c["text"] for c in chunks)


def test_small_table_rides_along_in_prose():
    chunks = chunk_doc("t", [mk("b1", filler(120, "P1")),
                             mk("b2", "| a | b |\n| 1 | 2 |", is_table=True),
                             mk("b3", filler(120, "P3"))])
    assert len(chunks) == 1
    assert chunks[0]["is_table"] is False
    assert "| a | b |" in chunks[0]["text"]


def test_big_table_stands_alone_whole():
    table = "\n".join(f"| row{i} | v{i} |" for i in range(150))  # >150 tokens
    chunks = chunk_doc("t", [mk("b1", filler(150, "P1")),
                             mk("b2", table, is_table=True),
                             mk("b3", filler(150, "P3"))])
    tc = [c for c in chunks if c["is_table"]]
    assert len(tc) == 1
    assert tc[0]["text"] == table          # whole, nothing appended
    assert tc[0]["block_ids"] == ["b2"]


def test_mixed_effective_date_inside_one_chunk_raises():
    with pytest.raises(ValueError):
        chunk_doc("t", [mk("b1", filler(150), eff="2020-01-01"),
                        mk("b2", filler(150), eff="2021-01-01")])