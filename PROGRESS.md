# Build Progress — RegRAG (9 Nov → 6 Dec 2026)

Deliverable focus comes straight from the spec's §9 build order. Dates glide
with sessions; the window end (Sun 6 Dec) does not.

| Day | Focus (ramayana) | Status |
| --- | --- | --- |
| D1 · Mon 9 Nov | repo+venv · spend cap · downloader+checksums · corpus chosen & verified | ✅ DONE |
| D2 · Tue 10 Nov | synthetic internal policy drafted + corpus-contract tests | ✅ DONE |
| D3–D4 · Wed–Thu 11–12 Nov | parser with page/section/effective-date metadata; 20-chunk hand-check per document ,parser v2, 405 blocks, 15 tests |✅DONE✅DONE|
| D5 · Fri 13 Nov | table extraction to markdown with page provenance (time-box ~6 h) | ☐ |
| D6 · Mon 16 Nov | chunker + automated chunk checks (no <100-token chunks; no split numbered clause) | ☐ |
| D7 · Tue 17 Nov | dense index (BGE-M3); measure embedding time | ☐ |
| D8 · Wed 18 Nov | BM25 over the same chunk ids; RRF fusion | ☐ |
| D9 · Thu 19 Nov | `evalkit`: Recall@k, MRR, nDCG@k, bootstrap CI, with tests | ☐ |
| D10 · Fri 20 Nov | golden set to 40 questions; retrieval scoring; first ablation rows | ☐ |
| D11 · Mon 23 Nov | cross-encoder reranker; measure CPU latency; keep-or-remove decision | ☐ |
| D12–D13 · Tue–Wed 24–25 Nov | generation: JSON contract, instruction hierarchy, quote-based citations | ☐ |
| D14 · Thu 26 Nov | citation validator; one retry; fallback to refusal | ☐ |
| D15 · Fri 27 Nov | judge rubric; hand-label 20 answers; judge agreement reported | ☐ |
| D16 · Mon 30 Nov | refusal threshold tuned on the unanswerable set | ☐ |
| D17 · Tue 1 Dec | PII redaction; 10-attack injection suite | ☐ |
| D18 · Wed 2 Dec | full evaluation run; `eval_report.md`; CI gate; break it once on purpose | ☐ |
| D19 · Thu 3 Dec | deploy; streaming UI; disclaimer; request caps + per-IP rate limit | ☐ |
| D20 · Fri 4 – Sun 6 Dec | README (full skeleton), architecture diagram, blog post, demo video; freeze Sat | ☐ |
