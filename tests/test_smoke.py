"""D1 smoke tests: the corpus list must be well-formed before anything downloads."""
from scripts.download_data import DOCS


def test_corpus_has_between_4_and_6_docs():
    assert 4 <= len(DOCS) <= 6


def test_every_doc_has_required_fields():
    for doc in DOCS:
        assert doc["doc_id"] and doc["title"] and doc["url"]
        assert doc["effective_date"] and doc["status"]


def test_effective_dates_are_iso():
    for doc in DOCS:
        assert len(doc["effective_date"]) == 10 and doc["effective_date"][4] == "-"


def test_urls_are_rbi_domain():
    for doc in DOCS:
        assert "rbi.org.in" in doc["url"]