"""D6: chunk every parsed doc + the synthetic policy into data/chunks/."""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regrag.ingest.chunk import chunk_doc, blocks_from_markdown, count_tokens

PARSED = ROOT / "data" / "parsed"
CHUNKS = ROOT / "data" / "chunks"
SYNTH = ROOT / "data" / "synthetic_policy_v1.md"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    CHUNKS.mkdir(exist_ok=True)
    jobs = [(f.stem.replace("_blocks", ""), load_jsonl(f))
            for f in sorted(PARSED.glob("*_blocks.jsonl"))]
    jobs.append(("synthetic_policy_v1", blocks_from_markdown(SYNTH, "synthetic_policy_v1")))

    for doc_id, blocks in jobs:
        chunks = chunk_doc(doc_id, blocks)
        out = CHUNKS / f"{doc_id}_chunks.jsonl"
        out.write_text("".join(json.dumps(c) + "\n" for c in chunks), encoding="utf-8")

        toks = [count_tokens(c["text"]) for c in chunks]
        tables = sum(1 for c in chunks if c["is_table"])
        sub_min = sum(1 for t in toks if t < 100)
        over_max = sum(1 for t, c in zip(toks, chunks) if t > 500 and not c["is_table"])
        print(f"{doc_id:26s} blocks={len(blocks):4d} chunks={len(chunks):4d} "
              f"tokens min/med/max={min(toks)}/{int(statistics.median(toks))}/{max(toks)} "
              f"tables={tables} sub-100={sub_min} prose-over-500={over_max}")


if __name__ == "__main__":
    main()