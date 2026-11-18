"""BM25 contract: tokenizer integrity, id alignment, deterministic ranking."""
from regrag.index import sparse


def test_tokenizer_keeps_identifiers_whole():
    toks = sparse.tokenize("Para 2.1.2 applies from 2025-05-08; Rs 10L limit.")
    assert "2.1.2" in toks
    assert "2025-05-08" in toks
    assert "2" not in toks, "section number must not fragment into page-noise"


def test_tokenizer_lowercases():
    assert sparse.tokenize("DLG Cover") == ["dlg", "cover"]


def test_ids_align_with_corpus_order():
    idx = sparse.SparseIndex()
    assert idx.ids == [c["chunk_id"] for c in sparse.load_chunks()]


def test_search_ranks_matching_chunk_first():
    chunks = [
        {"chunk_id": "d_c0001", "text": "repossession notice period before taking possession"},
        {"chunk_id": "d_c0002", "text": "cooling off period exit digital loan"},
        {"chunk_id": "d_c0003", "text": "provisioning doubtful assets three years"},
    ]
    idx = sparse.SparseIndex(chunks=chunks)
    hits = idx.search("cooling off period", k=3)
    assert hits[0]["chunk_id"] == "d_c0002"