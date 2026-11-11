"""RegRAG parser v2 (D3/D4).

PDF -> block records with full provenance. Every block answers:
which document, which page, which section, table or not, which version.

Record shape (one JSON object per block):
    block_id        stable id
    doc_id          from MANIFEST.json, never guessed from filename
    page            1-based physical page
    section_top     top-level section ("2. Guidelines...", "Chapter III")
    section         most specific heading found (may be a subsection "2.1 ...")
    text            extracted text (tables: pipe-joined rows)
    is_table        bool
    effective_date  from MANIFEST (human-verified version date)

v2 fixes, each traced to the D3 hand-check:
    1. mojibake roundtrip repair           (FPC/IRACP/DLD: 'â€™', 'â€“')
    2. heading length cap                  (KYC: '2. Accordingly...' bug)
    3. subsection headings tracked         (IRACP: '2.1 Non-performing Assets')
    4. letter sections tracked             (FPC: 'A. Applications...')
    5. footnotes / page numbers / vertical
       stamp lines dropped                 (all four docs)
    6. TOC blocks skipped                  (dotted leaders, front matter)
    7. table/text duplicate removal        (FPC index in two forms)

Known limitations (logged for the README):
    - inline vertical-stamp letters inside words (e.g. 'basWis') are not repaired
    - chapter names that merge with following text yield 'Chapter N' only
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
OUT = DATA / "parsed"

TOP_RE = re.compile(r"^(\d{1,2})\.\s+([A-Z][^.]{2,58})$")
SUB_RE = re.compile(r"^(\d{1,2}\.\d{1,2})\s+([A-Z][^.]{2,58})$")
LETTER_RE = re.compile(r"^([A-Z])\.\s+([A-Z][^.]{2,58})$")
CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLC]+)\b\s*(.*)$")
FOOTNOTE_RE = re.compile(r"^\d?\s?(Amended|Inserted)\s+vide")
PAGE_NO_RE = re.compile(r"^\d{1,3}$")
STAMP_RE = re.compile(r"^(?:[A-Za-z]\s+){4,}[A-Za-z]$")
INLINE_FN_RE = re.compile(r"(?<=\s)\d(?=[A-Z][a-z]{2,})")
DOTS_RE = re.compile(r"\.{5,}")
TOC_TITLE_RE = re.compile(r"^(index|contents|table of contents)\b", re.IGNORECASE)
NOISE_FLOOR = 25


def _fix_mojibake(line: str) -> str:
    """UTF-8 bytes mis-decoded as cp1252: re-encode wrong, decode right."""
    try:
        return line.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return line


def _nonlatin_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    non_latin = [c for c in letters if not ("a" <= c.lower() <= "z")]
    return len(non_latin) / len(letters)


def _keep(line: str) -> str | None:
    """Return the cleaned line, or None if it must be dropped."""
    s = line.strip()
    if not s:
        return None
    if FOOTNOTE_RE.match(s):
        return None
    if PAGE_NO_RE.match(s):
        return None
    if STAMP_RE.match(s):
        return None
    if _nonlatin_ratio(s) > 0.6:
        return None
    return INLINE_FN_RE.sub("", s)


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def _is_toc(text: str) -> bool:
    if TOC_TITLE_RE.match(text):
        return True
    if re.search(r"\.{10,}", text):
        return True
    return len(DOTS_RE.findall(text)) >= 3


def _make_block(doc_id, page, sec_top, sec, buf, eff, idx, is_table=False):
    text = " ".join(" ".join(buf).split()) if not is_table else buf
    if len(text) < NOISE_FLOOR:
        return None
    return {
        "block_id": f"{doc_id}_p{page:03d}_b{idx:03d}",
        "doc_id": doc_id,
        "page": page,
        "section_top": sec_top,
        "section": sec,
        "text": text,
        "is_table": is_table,
        "effective_date": eff,
    }


def parse_document(pdf_path: Path, entry: dict) -> tuple[list[dict], dict]:
    import pdfplumber

    doc_id, eff = entry["doc_id"], entry["effective_date"]
    blocks: list[dict] = []
    stats = {"toc_dropped": 0, "dup_tables_dropped": 0}
    section_top = section = None
    pending_chapter = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_no = page.page_number
            text_blocks: list[dict] = []
            idx = len(blocks)
            buf: list[str] = []

            def flush():
                nonlocal idx, buf, section_top, section, pending_chapter
                if not buf:
                    return
                idx += 1
                b = _make_block(doc_id, page_no, section_top, section, buf, eff, idx)
                buf = []
                if b is None:
                    return
                if _is_toc(b["text"]):
                    stats["toc_dropped"] += 1
                    return
                text_blocks.append(b)

            for raw in (page.extract_text() or "").split("\n"):
                line = _keep(raw)
                if line is None:
                    continue
                line = _fix_mojibake(line)

                m = CHAPTER_RE.match(line)
                if m:
                    flush()
                    pending_chapter = f"Chapter {m.group(1)}"
                    name = m.group(2).strip()
                    if name and len(name) <= 30 and not name[-1].isdigit():
                        section_top = section = f"{pending_chapter} - {name}"
                        pending_chapter = None
                    else:
                        section_top = section = pending_chapter
                    buf.append(line)
                    continue
                if pending_chapter and len(line) <= 40 and not line.endswith("."):
                    section = f"{pending_chapter} - {line}"
                    section_top = section
                    pending_chapter = None

                m = TOP_RE.match(line)
                if m:
                    flush()
                    section_top = f"{m.group(1)}. {m.group(2).rstrip()}"
                    section = section_top
                else:
                    m = SUB_RE.match(line)
                    if m:
                        flush()
                        section = f"{m.group(1)} {m.group(2).rstrip()}"
                    else:
                        m = LETTER_RE.match(line)
                        if m:
                            flush()
                            section = f"{m.group(1)}. {m.group(2).rstrip()}"
                buf.append(line)
            flush()

            tables = []
            for t in page.extract_tables():
                rows = ["|".join((c or "").strip() for c in row) for row in t]
                text = "\n".join(r for r in rows if r.strip())
                if len(text) >= NOISE_FLOOR and _nonlatin_ratio(text) <= 0.6:
                    tables.append(text)

            # dedupe: drop a text block that is mostly a copy of a table on this page
            dropped = set()
            for ti, ttext in enumerate(tables):
                tnorm = _norm(ttext)
                for bi, b in enumerate(text_blocks):
                    if bi in dropped or len(b["text"]) > 2 * len(ttext):
                        continue
                    frags = [f for f in re.split(r"[|,\n]", ttext) if len(f.strip()) > 4]
                    if frags and sum(1 for f in frags if _norm(f) in _norm(b["text"])) / len(frags) >= 0.6:
                        dropped.add(bi)
                        stats["dup_tables_dropped"] += 1
            for bi, b in enumerate(text_blocks):
                if bi not in dropped:
                    blocks.append(b)
            for ttext in tables:
                idx += 1
                blocks.append(_make_block(doc_id, page_no, section_top, section, ttext, eff, idx, is_table=True))

    for i, b in enumerate(blocks, start=1):
        b["block_id"] = f"{b['doc_id']}_p{b['page']:03d}_b{i:03d}"
    return blocks, stats


def main() -> int:
    manifest = json.loads((DATA / "MANIFEST.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    total = 0
    for entry in manifest["docs"]:
        blocks, stats = parse_document(DATA / entry["file"], entry)
        out_file = OUT / f"{entry['doc_id']}_blocks.jsonl"
        with out_file.open("w", encoding="utf-8") as f:
            for b in blocks:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")
        n_tables = sum(1 for b in blocks if b["is_table"])
        sections = len({b["section"] for b in blocks if b["section"]})
        total += len(blocks)
        print(f"{entry['doc_id']}: {len(blocks)} blocks ({n_tables} tables, "
              f"{sections} sections; toc dropped: {stats['toc_dropped']}, "
              f"dups dropped: {stats['dup_tables_dropped']})")
    print(f"\ntotal blocks: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())