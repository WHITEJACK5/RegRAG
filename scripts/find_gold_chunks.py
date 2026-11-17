
"""Suggest gold_chunks candidates for each golden entry.
Assistive search only - every mapping must be human-confirmed."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "golden" / "golden_set_v1.jsonl"
CHUNK_DIR = ROOT / "data" / "chunks"

STOP = set(("a an and are as at be by for from has have in is it its of on or "
            "that the to was were will shall with not no than then this these "
            "those under per any all such their there which who whom whose when "
            "where what how why").split())


def norm(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9%₹]+", text.lower())
    return [w for w in words if w not in STOP and len(w) > 1]


def main() -> None:
    chunks = []
    for f in sorted(CHUNK_DIR.glob("*_chunks.jsonl")):
        chunks += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    for c in chunks:
        c["_words"] = set(norm(c["text"]))

    entries = [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines() if l.strip()]
    for e in entries:
        if e["type"] == "unanswerable":
            continue
        qw = set(norm(e["question"]))
        facts = e.get("key_facts", [])
        scored = []
        for c in chunks:
            hits = sum(1 for f in facts if all(w in c["_words"] for w in norm(f)))
            overlap = len(qw & c["_words"]) / max(len(qw), 1)
            if hits or overlap > 0.2:
                scored.append((hits, round(overlap, 2), c["chunk_id"], c["pages"]))
        scored.sort(reverse=True)
        print(f"\n{e['q_id']} [{e['type']}] {e['question']}")
        for hits, ov, cid, pages in scored[:5]:
            print(f"   {cid:34s} facts={hits}/{len(facts)} q_overlap={ov} pages={pages}")
    print("\nSuggestions, not answers. Read each candidate chunk before recording it.")


if __name__ == "__main__":
    main()