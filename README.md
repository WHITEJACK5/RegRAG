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
- Page-spanning tables keep only the fragment on their page; the header row
  stays behind on the previous page.
- Boxed paragraphs are demoted to text by a cell-length heuristic; a genuine
  small table with long cells could be misdemoted.
- Footnote text interleaves into body paragraphs at page boundaries in DLD
  and IRACP chunks; footnote markers appear mid-paragraph instead of apart.
- Page-spanning tables are sliced per page by the parser; each slice is
  under the 150-token small-table threshold, so logical tables ride along
  in prose chunks and slices can split across chunk boundaries (KYC).

## Golden set

data/golden/golden_set_v1.jsonl holds the evaluation questions (target: 40 +
5 friend-written). Rules: gold answers only from parsed blocks you have read;
answerable entries carry doc/page/section provenance; unanswerables have null
gold and a recorded silence search. Guarded by tests/test_golden_set.py.
Track coverage: python scripts/golden_inventory.py
