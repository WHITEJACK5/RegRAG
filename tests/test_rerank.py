"""Contract tests for reranking: no model download, no forward pass."""
import pytest

from regrag.retrieve.rerank import rerank


class FakeEncoder:
    """Returns preset scores in candidate order and records every call."""

    def __init__(self, scores):
        self.scores = list(scores)
        self.calls = []

    def predict(self, pairs, batch_size=16, show_progress_bar=False):
        self.calls.append({"pairs": list(pairs), "batch_size": batch_size})
        return self.scores[: len(pairs)]


CANDIDATES = [
    {"chunk_id": "a", "score": 0.9},
    {"chunk_id": "b", "score": 0.8},
    {"chunk_id": "c", "score": 0.7},
]
TEXTS = {"a": "alpha", "b": "beta", "c": "gamma"}


def test_rerank_orders_by_cross_encoder_score():
    out = rerank("q", CANDIDATES, TEXTS, FakeEncoder([0.1, 0.9, 0.5]), top_n=2)
    assert [x["chunk_id"] for x in out] == ["b", "c"]
    assert out[0]["score"] == pytest.approx(0.9)


def test_ties_break_by_chunk_id():
    reverse = [{"chunk_id": "c"}, {"chunk_id": "a"}, {"chunk_id": "b"}]
    out = rerank("q", reverse, TEXTS, FakeEncoder([0.5, 0.5, 0.5]), top_n=3)
    assert [x["chunk_id"] for x in out] == ["a", "b", "c"]


def test_missing_text_raises_before_the_model_is_called():
    fake = FakeEncoder([1.0])
    with pytest.raises(KeyError, match="b"):
        rerank("q", [{"chunk_id": "a"}, {"chunk_id": "b"}], {"a": "alpha"}, fake)
    assert fake.calls == []


def test_rerank_does_not_mutate_candidates():
    before = [dict(c) for c in CANDIDATES]
    rerank("q", CANDIDATES, TEXTS, FakeEncoder([0.3, 0.2, 0.1]))
    assert CANDIDATES == before


def test_empty_pool_returns_empty_without_calling_the_model():
    fake = FakeEncoder([])
    assert rerank("q", [], {}, fake) == []
    assert fake.calls == []