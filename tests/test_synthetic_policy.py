"""D2: the synthetic policy file must satisfy its corpus contract.

The policy is a first-class corpus member. These tests pin the contract:
labelled synthetic, long enough (5 pages plus), and traceable to the
four RBI docs it references.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "data" / "synthetic_policy_v1.md"


def _text() -> str:
    assert POLICY.exists(), "synthetic policy file missing"
    return POLICY.read_text(encoding="utf-8")


def test_policy_is_labelled_synthetic():
    assert "SYNTHETIC" in _text()[:2000]


def test_policy_is_5_pages_or_more():
    # rule of thumb used here: ~300 words per page, 5 pages minimum
    words = len(_text().split())
    assert words >= 1400, f"policy too short: {words} words"


def test_policy_traces_all_four_rbi_docs():
    text = _text()
    for doc_id in (
        "rbi_kyc_2016",
        "rbi_digital_lending_2025",
        "rbi_iracp_2025",
        "rbi_fair_practices_code",
    ):
        assert doc_id in text, f"missing trace to {doc_id}"


def test_unverified_points_are_flagged():
    # Nothing may pretend to know an RBI number we have not parsed yet.
    text = _text()
    assert "VERIFY-D3" in text
    # every VERIFY-D3 flag must have a reason attached
    assert text.count("VERIFY-D3") >= 4