"""Golden-set contract tests: the exam file is guarded like the manifest.

A typo in a gold answer poisons every future evaluation silently - a wrong
gold_page makes honest citations look wrong, a mistyped type breaks scoring.
So the golden set gets the same treatment as the parser output: invariants,
enforced by code, independent of any console.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden" / "golden_set_v1.jsonl"
MANIFEST = ROOT / "data" / "MANIFEST.json"

REQUIRED_KEYS = {"q_id", "type", "question", "gold_answer",
                 "gold_doc", "gold_page", "gold_section", "notes"}
ALLOWED_TYPES = {"lookup", "multihop", "numeric", "unanswerable"}


def _rows():
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


def test_every_row_has_full_schema():
    for r in _rows():
        assert REQUIRED_KEYS <= set(r), f"{r.get('q_id')}: missing keys"


def test_q_ids_are_unique():
    ids = [r["q_id"] for r in _rows()]
    assert len(ids) == len(set(ids)), "duplicate q_id"


def test_types_are_from_allowed_set():
    bad = [r["q_id"] for r in _rows() if r["type"] not in ALLOWED_TYPES]
    assert not bad, f"bad type in {bad}"


def test_answerables_have_gold_answer_and_provenance():
    for r in _rows():
        if r["type"] == "unanswerable":
            continue
        assert r["gold_answer"], f"{r['q_id']}: missing gold_answer"
        assert r["gold_doc"] and r["gold_page"], \
            f"{r['q_id']}: missing gold_doc/gold_page"


def test_gold_doc_exists_in_corpus():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc_ids = {d["doc_id"] for d in manifest["docs"]} | {"synthetic_policy_v1"}
    bad = [r["q_id"] for r in _rows()
           if r["type"] != "unanswerable" and r["gold_doc"] not in doc_ids]
    assert not bad, f"gold_doc not in corpus: {bad}"


def test_unanswerables_refuse_cleanly():
    for r in _rows():
        if r["type"] == "unanswerable":
            assert r["gold_answer"] is None and r["gold_doc"] is None, \
                f"{r['q_id']}: unanswerable must have null gold"


def test_unanswerables_document_their_silence():
    for r in _rows():
        if r["type"] == "unanswerable":
            assert len(r.get("notes", "")) > 40, \
                f"{r['q_id']}: unanswerable must record WHY the corpus is silent"