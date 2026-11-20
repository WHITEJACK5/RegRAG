"""Contract tests for the ablation summariser: no model, no index."""
import pytest

from regrag.eval.report import markdown, summarize

ROWS = [
    {"q_id": "Q1", "type": "lookup", "gold_chunks": ["a"]},
    {"q_id": "Q2", "type": "lookup", "gold_chunks": ["b"]},
    {"q_id": "Q3", "type": "multihop", "gold_chunks": ["c", "d"]},
    {"q_id": "Q4", "type": "numeric", "gold_chunks": ["e"]},
]

RANK = {
    "Q1": {"dense": ["a"], "hybrid": ["a"]},
    "Q2": {"dense": ["x", "b"], "hybrid": ["b"]},
    "Q3": {"dense": ["c", "x"], "hybrid": ["c", "d"]},
    "Q4": {"dense": ["x"], "hybrid": ["e"]},
}


def test_overall_means_match_hand_arithmetic():
    res = summarize(ROWS, RANK, ("dense", "hybrid"), k=6)
    # dense recall: 1.0, 1.0, 0.5, 0.0 -> 0.625
    assert res["dense"]["overall"]["n"] == 4
    assert res["dense"]["overall"]["recall"]["mean"] == pytest.approx(0.625)
    # hybrid finds every gold chunk in the top 6
    assert res["hybrid"]["overall"]["recall"]["mean"] == pytest.approx(1.0)


def test_slices_count_the_right_rows():
    res = summarize(ROWS, RANK, ("dense", "hybrid"), k=6)
    assert res["dense"]["lookup"]["n"] == 2
    assert res["dense"]["multihop"]["n"] == 1
    assert res["dense"]["numeric"]["n"] == 1


def test_interval_brackets_each_mean_and_markdown_has_rows():
    res = summarize(ROWS, RANK, ("dense", "hybrid"), k=6)
    for by_type in res.values():
        for block in by_type.values():
            for metric in ("recall", "mrr", "ndcg"):
                m = block[metric]
                assert m["lo"] <= m["mean"] <= m["hi"]
    table = markdown(res, k=6)
    assert "| overall | dense | 4 |" in table
    assert "| multihop | hybrid | 1 |" in table