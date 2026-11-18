"""Compare dense, BM25 and RRF-fused retrieval for one query."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentence_transformers import SentenceTransformer

from regrag.index import dense
from regrag.index.sparse import SparseIndex
from regrag.retrieve.hybrid import rrf_fuse


def main() -> None:
    query = " ".join(sys.argv[1:]) or "cooling-off period digital loan"
    index, ids = dense.load_index()
    model = SentenceTransformer(dense.MODEL_NAME)
    dense_hits = dense.search(index, ids, model, query, k=30)
    sparse = SparseIndex()
    bm25_hits = sparse.search(query, k=30)
    fused = rrf_fuse([dense_hits, bm25_hits], top_n=6)

    print(f"query: {query}")
    print("\nDENSE top-6")
    for r in dense_hits[:6]:
        print(f"  {r['score']:.4f}  {r['chunk_id']}")
    print("\nBM25 top-6")
    for r in bm25_hits[:6]:
        print(f"  {r['score']:7.3f}  {r['chunk_id']}")
    print("\nRRF fused top-6")
    for r in fused:
        print(f"  {r['score']:.5f}  {r['chunk_id']}")


if __name__ == "__main__":
    main()