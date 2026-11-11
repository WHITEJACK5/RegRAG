"""Golden-set inventory: per-type coverage toward the spec's 40-entry target."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden" / "golden_set_v1.jsonl"
TARGETS = {"lookup": 14, "multihop": 10, "numeric": 8, "unanswerable": 8}


def main() -> int:
    rows = [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    counts = Counter(r["type"] for r in rows)
    print(f"Golden set - {GOLDEN.name}")
    print(f"  total entries    {len(rows)} / 40 (+5 friend-written later)")
    for t, target in TARGETS.items():
        print(f"  {t:<13} {counts.get(t, 0):>3} / {target:<3} {'#' * counts.get(t, 0)}")
    missing = sum(max(0, target - counts.get(k, 0)) for k, target in TARGETS.items())
    print(f"  remaining to write: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())