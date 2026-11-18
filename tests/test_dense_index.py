"""Dense-index contract tests, run against a deterministic fake encoder."""
import json
from pathlib import Path

import numpy as np
import pytest

from regrag.index import dense


class FakeEncoder:
    """Deterministic tiny encoder: 8 dims from the first 8 characters."""

    name_or_path = "fake-encoder"

    def encode(self, texts, **kwargs):
        vecs = []
        for t in texts:
            v = np.zeros(8, dtype="float32")
            for i, ch in enumerate(t[:8].ljust(8)):
                v[i] = (ord(ch) % 97) / 97.0
            norm = np.linalg.norm(v) or 1.0
            vecs.append(v / norm)
        return np.array(vecs, dtype="float32")


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(dense, "INDEX_DIR", tmp_path)
    monkeypatch.setattr(dense, "INDEX_FILE", tmp_path / "dense.faiss")
    monkeypatch.setattr(dense, "IDS_FILE", tmp_path / "dense_ids.json")
    monkeypatch.setattr(dense, "META_FILE", tmp_path / "dense_meta.json")
    return tmp_path


def test_build_persists_index_ids_and_meta(sandbox):
    meta = dense.build_index(model=FakeEncoder())
    assert (sandbox / "dense.faiss").exists()
    assert (sandbox / "dense_ids.json").exists()
    assert (sandbox / "dense_meta.json").exists()
    assert meta["num_chunks"] == len(dense.load_chunks())
    assert meta["dim"] == 8


def test_ids_align_exactly_with_chunk_corpus(sandbox):
    dense.build_index(model=FakeEncoder())
    _, ids = dense.load_index()
    expected = [c["chunk_id"] for c in dense.load_chunks()]
    assert ids == expected, "row order and chunk ids must match one-to-one"


def test_search_returns_valid_sorted_results(sandbox):
    dense.build_index(model=FakeEncoder())
    index, ids = dense.load_index()
    results = dense.search(index, ids, FakeEncoder(), "cooling off period", k=6)
    assert 0 < len(results) <= 6
    assert all(r["chunk_id"] in ids for r in results)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), "results must be best-first"
    assert all(-1.001 <= s <= 1.001 for s in scores), "cosine scores"


def test_load_index_rejects_ids_index_mismatch(sandbox):
    dense.build_index(model=FakeEncoder())
    ids = json.loads((sandbox / "dense_ids.json").read_text(encoding="utf-8"))
    (sandbox / "dense_ids.json").write_text(json.dumps(ids[:-1]), encoding="utf-8")
    with pytest.raises(ValueError):
        dense.load_index()