"""regrag/ingest/chunk.py — D6 section-aware, table-aware chunker.

Contract (SPEC §5, §9-D6): chunks ~300-500 tokens, ~15% overlap,
section-aware, table-aware, never split a numbered clause,
no chunk under 100 tokens.

Token accounting: 1 token ~= 1 whitespace word. English regulatory
prose has more BPE tokens than words, so word-count UNDERestimates:
our chunks run slightly fatter than labeled. Fat is safe.
"""
from __future__ import annotations

import re
from pathlib import Path

TARGET_TOKENS = 400          # midpoint of the spec's 300-500 window
MAX_TOKENS = 500             # hard ceiling for prose chunks
MIN_TOKENS = 100             # spec floor: no chunk under this
OVERLAP_TOKENS = 60          # ~15% of TARGET, applied at split boundaries
SMALL_TABLE_MAX = 150        # tables this small ride along inside prose chunks
PIECE_MAX = MAX_TOKENS - OVERLAP_TOKENS  # leave room for the overlap tail

_SYNTH_EFFECTIVE_RE = re.compile(r"^effective_date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)

# Boundaries where a split is legal: numbered-clause starts and sentence starts.
_CLAUSE_START = re.compile(
    r"(?:^|\s)(?:"
    r"\((?:i{1,3}|iv|vi{1,3}|ix|x|[a-z]|\d{1,2})\)"   # (i) (ii) (a) (1)
    r"|(?:i{1,3}|iv|vi{1,3}|ix|x)\."                   #  i.  ii.
    r"|\d+(?:\.\d+)+(?=\s)"                            # 4.2.19.2
    r")",
    re.IGNORECASE,
)


def count_tokens(text: str) -> int:
    """Our token proxy: whitespace words."""
    return len(text.split())


def _atoms(text: str) -> list[str]:
    """Cut text into atomic pieces at clause/sentence starts. Atoms stay whole."""
    bounds = {0, len(text)}
    for m in _CLAUSE_START.finditer(text):
        s = m.start()
        while s < len(text) and text[s].isspace():
            s += 1
        if 0 < s < len(text):
            bounds.add(s)
    for m in re.finditer(r"(?<=[.!?])\s+", text):
        bounds.add(m.end())
    ordered = sorted(bounds)
    return [t for t in (text[a:b].strip() for a, b in zip(ordered, ordered[1:])) if t]


def _split_with_overlap(text: str) -> list[str]:
    """Split one oversized text block into pieces <= PIECE_MAX tokens,
    cutting only at atomic boundaries, with ~OVERLAP words duplicated
    between consecutive pieces. Every clause stays whole in >=1 piece."""
    pieces: list[str] = []
    cur: list[str] = []
    cur_n = 0
    for atom in _atoms(text):
        n = count_tokens(atom)
        if n > PIECE_MAX:  # pathological: a single clause longer than a piece
            if cur:
                pieces.append(" ".join(cur))
                cur, cur_n = [], 0
            words = atom.split()
            pieces.extend(" ".join(words[k:k + PIECE_MAX]) for k in range(0, len(words), PIECE_MAX))
            continue
        if cur and cur_n + n > PIECE_MAX:
            pieces.append(" ".join(cur))
            tail = " ".join(cur).split()[-OVERLAP_TOKENS:]
            cur = [" ".join(tail)] if tail else []
            cur_n = len(tail)
        cur.append(atom)
        cur_n += n
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def _units(blocks: list[dict]):
    """Turn parsed blocks into packing units.

    - big table (> SMALL_TABLE_MAX): atomic standalone unit
    - oversized text (> MAX_TOKENS): clause-respecting pieces with overlap
    - everything else: passes through whole
    """
    for blk in blocks:
        n = count_tokens(blk["text"])
        if blk.get("is_table") and n > SMALL_TABLE_MAX:
            yield {**blk, "unit_tokens": n, "big_table": True}
        elif n > MAX_TOKENS:
            for j, piece in enumerate(_split_with_overlap(blk["text"])):
                yield {**blk, "text": piece, "unit_tokens": count_tokens(piece),
                       "big_table": False, "piece": j}
        else:
            yield {**blk, "unit_tokens": n, "big_table": False}


def _close(doc_id: str, cur: dict) -> dict:
    blocks = cur["blocks"]
    dates = {b["effective_date"] for b in blocks}
    if len(dates) > 1:
        raise ValueError(f"{doc_id}: mixed effective_date inside one chunk: {dates}")
    return {
        "doc_id": doc_id,
        "section": cur["section"],
        "pages": sorted({b["page"] for b in blocks}),
        "is_table": bool(cur.get("is_table")),
        "effective_date": blocks[0]["effective_date"],
        "block_ids": [b["block_id"] for b in blocks],
        "text": "\n\n".join(b["text"] for b in blocks),
    }


def chunk_doc(doc_id: str, blocks: list[dict]) -> list[dict]:
    """Greedily pack units into chunks. Break when: section changes, or
    the next unit would push us past MAX_TOKENS — but only once the
    current chunk is already >= MIN_TOKENS (the floor outranks purity)."""
    raw: list[dict] = []
    cur: dict | None = None

    for u in _units(blocks):
        if u["big_table"]:
            if cur is not None and cur["tokens"] >= MIN_TOKENS:
                raw.append(_close(doc_id, cur))
                cur = None
            raw.append(_close(doc_id, {"blocks": [u], "section": u["section"],
                                       "tokens": u["unit_tokens"], "is_table": True}))
            continue

        if cur is None:
            cur = {"blocks": [], "section": u["section"], "tokens": 0, "is_table": False}
        section_change = u["section"] != cur["section"]
        would_overflow = cur["tokens"] + u["unit_tokens"] > MAX_TOKENS
        if (section_change or would_overflow) and cur["tokens"] >= MIN_TOKENS:
            raw.append(_close(doc_id, cur))
            cur = {"blocks": [], "section": u["section"], "tokens": 0, "is_table": False}
        cur["blocks"].append(u)
        cur["tokens"] += u["unit_tokens"]
        cur["section"] = u["section"]  # a sub-MIN tail may merge forward across sections

    if cur is not None:
        if cur["tokens"] < MIN_TOKENS and raw:
            # doc-final orphan: merge backward into the previous chunk
            prev = raw[-1]
            prev["block_ids"] += [b["block_id"] for b in cur["blocks"]]
            prev["pages"] = sorted(set(prev["pages"]) | {b["page"] for b in cur["blocks"]})
            prev["text"] += "\n\n" + "\n\n".join(b["text"] for b in cur["blocks"])
        else:
            raw.append(_close(doc_id, cur))

    return [{**c, "chunk_id": f"{doc_id}_c{i:04d}"} for i, c in enumerate(raw)]


def blocks_from_markdown(md_path: Path, doc_id: str) -> list[dict]:
    """Synthetic policy (.md) -> block dicts with the same schema as parsed
    PDF blocks, so ONE chunker serves all five documents. page=0 means
    'no page' (synthetic doc); the effective_date must be declared by a
    human in the file header — the machine never guesses it."""
    text = md_path.read_text(encoding="utf-8")
    m = _SYNTH_EFFECTIVE_RE.search(text)
    if not m:
        raise SystemExit(
            f"{md_path}: add a header line 'effective_date: YYYY-MM-DD' "
            f"so the chunker can stamp the synthetic doc."
        )
    eff = m.group(1)
    body = _SYNTH_EFFECTIVE_RE.sub("", text, count=1)

    blocks: list[dict] = []
    section = doc_id
    text_buf: list[str] = []
    table_buf: list[str] = []

    def flush_text() -> None:
        nonlocal text_buf
        para = "\n".join(text_buf).strip()
        if para:
            blocks.append({"block_id": "", "doc_id": doc_id, "page": 0,
                           "section": section, "text": para,
                           "is_table": False, "effective_date": eff})
        text_buf = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            blocks.append({"block_id": "", "doc_id": doc_id, "page": 0,
                           "section": section, "text": "\n".join(table_buf),
                           "is_table": True, "effective_date": eff})
        table_buf = []

    for line in body.splitlines():
        s = line.strip()
        if s.startswith("#"):
            flush_text(); flush_table()
            section = s.lstrip("#").strip() or section
        elif s.startswith("|"):
            flush_text()
            table_buf.append(s)
        elif s == "":
            flush_text(); flush_table()
        else:
            flush_table()
            text_buf.append(line.rstrip())
    flush_text(); flush_table()

    for i, b in enumerate(blocks):
        b["block_id"] = f"{doc_id}_b{i:04d}"
    return blocks