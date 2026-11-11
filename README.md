# RegRAG

Citation-grounded question answering over Indian retail-lending regulation
(RBI Master Directions / circulars) and a synthetic internal lending policy.

**Claim:** every answer carries page-level citations with a verbatim quote that
code verifies; when the corpus does not support an answer, the system refuses.

**Status:** early build (D2 of 20 · 9 Nov – 6 Dec 2026). Full README with
results, evaluation and ablation tables lands at the end of the build window.

- Educational project. Not legal or financial advice.
- Public RBI documents; PDFs are never committed to git (see `data/MANIFEST.json`
  for checksums, effective dates and statuses).
- Corpus so far: 4 verified RBI documents + the synthetic internal policy
  `data/synthetic_policy_v1.md` (design notes in `docs/CORPUS.md`).

## Known limitations (parser v2)

- Vertical margin-stamp letters ("With effect from...") interleaved inside
  words are not repaired (e.g. 'basWis', 'Directioans'); whole stamp lines
  are dropped.
- Chapter headings that merge with body text record as 'Chapter N' only.
- TOC content sharing a flushed block with a cover page is dropped whole.
- Some footnote text riding at the end of page-final blocks is retained.
