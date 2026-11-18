"""Print the four retrieval metrics on a hand-checkable toy ranking."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regrag.eval.evalkit import bootstrap_ci, mrr, ndcg_at_k, recall_at_k


def main() -> None:
    retrieved = ["b", "c", "a"]
    gold = ["a"]
    print("retrieved:", retrieved)
    print("gold:     ", gold)
    print(f"Recall@6: {recall_at_k(retrieved, gold, k=6):.3f}")
    print(f"MRR:      {mrr(retrieved, gold):.3f}")
    print(f"nDCG@6:   {ndcg_at_k(retrieved, gold, k=6):.3f}")
    lo, hi = bootstrap_ci([0.0, 0.5, 1.0], n_boot=1000, seed=7)
    print(f"bootstrap 95% CI for [0.0, 0.5, 1.0]: [{lo:.3f}, {hi:.3f}]")


if __name__ == "__main__":
    main()