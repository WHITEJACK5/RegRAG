"""Build the dense index and report the measured embedding time (D7 deliverable)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import time

from regrag.index import dense


def main() -> None:
    t0 = time.perf_counter()
    meta = dense.build_index()
    total = time.perf_counter() - t0
    print(f"model={meta['model']}  dim={meta['dim']}  chunks={meta['num_chunks']}")
    print(f"model load : {meta['model_load_seconds']:>8.2f} s")
    print(f"embedding  : {meta['embed_seconds']:>8.2f} s   "
          f"({meta['embed_chunks_per_second']} chunks/s)")
    print(f"total      : {round(total, 2)} s")
    print("persisted: data/index/dense.faiss + dense_ids.json + dense_meta.json")


if __name__ == "__main__":
    main()