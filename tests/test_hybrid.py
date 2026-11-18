"""RRF contract: formula, rank-only fusion, agreement beats a lone first place."""
from regrag.retrieve.hybrid import rrf_fuse


def _ranking(*ids):
    return [{"chunk_id": cid, "score": 0.0} for cid in ids]


def test_rrf_formula_single_list():
    fused = rrf_fuse([_ranking("a", "b")], k=60, top_n=2)
    assert fused[0]["chunk_id"] == "a"
    assert abs(fused[0]["score"] - 1 / 61) < 1e-12
    assert abs(fused[1]["score"] - 1 / 62) < 1e-12


def test_agreement_beats_single_first_place():
    fused = rrf_fuse([_ranking("a", "b", "c"), _ranking("b", "c", "a")],
                     k=60, top_n=3)
    assert fused[0]["chunk_id"] == "b", "two lists agree on b; a is first only once"


def test_fusion_ignores_score_magnitudes():
    r1 = [{"chunk_id": "a", "score": 0.99}, {"chunk_id": "b", "score": 0.01}]
    r2 = [{"chunk_id": "a", "score": 7.70}, {"chunk_id": "b", "score": 0.20}]
    assert rrf_fuse([r1], top_n=2) == rrf_fuse([r2], top_n=2)