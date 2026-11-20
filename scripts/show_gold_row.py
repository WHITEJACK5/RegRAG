"""Print a golden-set row beside the full text of every chunk it cites."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden" / "golden_set_v1.jsonl"


def load_rows():
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


def load_chunks():
    chunks = {}
    for f in sorted((ROOT / "data" / "chunks").glob("*_chunks.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                c = json.loads(line)
                chunks[c["chunk_id"]] = c
    return chunks


def main(argv):
    rows = {r["q_id"]: r for r in load_rows()}
    missing = [q for q in argv if q not in rows]
    if missing:
        raise SystemExit(f"unknown q_id: {missing}")
    chunks = load_chunks()
    for qid in argv:
        r = rows[qid]
        print("=" * 78)
        print(f"{qid} | {r['type']} | {r['gold_doc']} p.{r['gold_page']}")
        print("Q:", r["question"])
        print("A:", r["gold_answer"])
        print("key_facts:", r["key_facts"])
        for cid in r["gold_chunks"]:
            c = chunks[cid]
            print("-" * 78)
            print(f"{cid} | pages {c['pages']} | {c['section']}")
            print(c["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))