# Decision log — RegRAG

One entry per real decision, newest at the bottom. This is the raw material
for the README's "Why these choices" section and for interview stories.

## D1 · Mon 9 Nov 2026

- Generation LLM: **Google Gemini** — free tier now (cap by construction:
  no billing), paid spend cap set before D12; model `gemini-2.5-flash`
  pending a pricing re-check at generation time.
- Corpus = 4 RBI docs + 1 synthetic policy (within the spec's 4–6 range).
- Downloader needs browser-like headers (incl. `Referer: https://www.rbi.org.in/`)
  to defeat RBI's bot-wall; validated by diffing bare-UA vs browser-UA
  responses (bare returned HTML, browser returned `application/pdf`).
- Python 3.11.9, venv; dependencies grow per-week, never pre-installed.

## D2 · Tue 10 Nov 2026

- Synthetic policy: SahiCredit Finance Pvt Ltd; products = personal + vehicle
  - consumer durables; **LTI ≤ 40%**; **aggregate ticket ≤ ₹10L**;
    **grievance TAT 7 working days** — deliberately stricter than the baseline
    to create honest multi-hop questions.
- Tests-before-satisfaction: the 5-page floor test FAILED the v1 draft
  (1,251 words). The document was extended with real substance (named fee
  schedule, LSP governance, repossession conduct, complaint category
  discipline) — the gate was not lowered.
- Policy numerical values accepted as written by the owner (recorded in the
  policy's version note).

## D3 — Package layout (2026-11-11)

regrag/ is the Python package (library code); scripts/ are thin CLI entry points.
Library code must be importable and testable without a shell; scripts exist so a
human can run one thing from PowerShell.

## D3 — effective_date lives in MANIFEST.json (2026-11-11)

The version date is human-verified and stored in the manifest; the parser only
inherits it. The FPC PDF carried three conflicting dates (filename, metadata,
letterhead); a parser would have to guess. The PDF is frozen evidence; the
manifest is the judgment.

## D3 — "Mojibake" was a console artifact (2026-11-12)

The parsed JSONL files were always clean UTF-8; the a^~-sequences came from
PowerShell Get-Content decoding UTF-8 files with the ANSI (cp1252) codec at
display time. Proof: Get-Content -Encoding UTF8 and Python print both show
correct characters; every fake run was exactly 3 chars = 3 UTF-8 bytes of one
correct character. Lesson: verify at the layer where the defect lives.
\_fix_mojibake stays as insurance (no-op on clean text).

## D4 — Golden set conventions (2026-11-12)

One JSON object per line; q_ids ordered G###. Four types: lookup, multihop,
numeric, unanswerable (target mix 14/10/8/8 + 5 friend-written). The schema
holds ONE primary gold_doc even for multihops; the second source lives in
notes and the eval scorer must check both. Unanswerables have null gold
fields, expect refusal, and must record which blocks were checked.

## D4 — Verified silence (2026-11-12)

An "unanswerable" claim is itself a factual claim. G005's silence was verified
with Select-String across the policy and all parsed blocks before entry.
Habit: no unanswerable enters the set without a recorded search.

## D5 — Prose-table demotion (2026-11-13)

pdfplumber captures RBI's boxed paragraphs as tables (drawn borders trigger
extract_tables). About half of IRACP's "101 tables" were boxed prose. Rule:
a captured table whose cells are mostly >80-char sentences is prose and is
relabeled is_table=false. Evidence: 10 hand-audited blocks; heuristic agreed
with all 10. Also fixed: demoted strings hit \_make_block's list-join branch
(" ".join on a string shreds characters) - lay dormant for 2 days until the
first string ever reached that branch. Lesson: new data paths need a test.

## D5 — Golden set adopts guide section 11 fields (2026-11-13)

key_facts (2-4 short strings the answer must contain) added to all entries;
the judge will score answer correctness against them. gold_chunks will be
filled when the chunker (D6) creates chunk ids. Note: the "9 commits at day
end" rule is our own working agreement from D1 - neither ramayana document
prescribes commit cadence.

"Doc-id convention: the 5th corpus member is synthetic_policy_v1 everywhere (tests, chunks, gold). The md's own metadata table said synthetic_internal_policy; aligned file to contract, 16 Nov."

## D6 — Chunker packing rules (2026-11-16)

Token ≈ whitespace word. TARGET=400 / MAX=500 / MIN=100 tokens; 60-token
(~15%) overlap only at split boundaries, never inside intact blocks. Tables
≤150 tokens ride along with surrounding prose; larger tables stand alone
whole. Sub-MIN blocks merge forward into the next block group; the document's
final tail merges backward. Output: 236 chunks across 5 docs, deterministic,
every block covered exactly once.

## D6 — Merge-forward section labels lag (2026-11-16)

Synthetic policy section 8 (~90 tokens) fell under the MIN floor and merged
forward into section 9's chunk; the chunk `section` label takes the LAST
section, so it reads "9." while carrying section 8's text. First live
sighting of the merge-forward rule. Accepted: text is intact, only the label
is imprecise — retrieval works on text, not labels.

## D6 — Page-sliced tables never stand alone (2026-11-16)

The parser slices page-spanning tables per page (KYC FPI tables: b120=108w,
b121=77w, ...). Each slice is under the 150-token small-table threshold, so
each correctly rides along in prose — with the consequence that a big
logical table NEVER becomes a standalone chunk and its slices can split
across chunk boundaries (b120+b121 shared c0099 only by luck). New nuance
of the known page-spanning-table limitation. Lesson: inspect the unit, not
the bundle — I mis-sized b120 from the chunk text instead of the block.

## D6 — Synthetic effective_date corrected (2026-11-16)

The md carried placeholder `effective_date: 2026-01-01`, contradicting its
own metadata table. Hand-check caught it; corrected to 2026-11-10. The
header is human-declared and loader-verified because a wrong version date
poisons every inherited chunk silently.

## D7 — Dense index design (2026-11-19)

BGE-M3 (1024 dims), L2-normalised vectors into FAISS IndexFlatIP. With unit
vectors the inner product IS cosine similarity, so no metric bookkeeping and
no score rescaling anywhere downstream; scores land in [-1, 1]. Exact search
on purpose: 236 vectors is ~1 MB, brute force costs microseconds, and an ANN
index's silent recall loss would poison every ablation number in D10.
FAISS returns row numbers, not chunk ids; data/index/dense_ids.json is the
persisted row->id map and load_index() refuses a length mismatch - a
desynchronised map returns confidently wrong chunks, the worst failure mode
retrieval has. The model is injectable so tests exercise the pipeline
against a deterministic fake encoder in milliseconds.

## D7 — Measured embedding cost (2026-11-19)

236 chunks, CPU-only, sentence-transformers 6.3.0: model load 8.17 s,
embedding 2563.30 s (42:43, 0.09 chunks/s, ~10.9 s/chunk). An earlier
identical run displayed 1953 s (32:33): 31% slower for the same work,
consistent with thermal throttling on a long CPU-bound job - we record the
slower instrumented number. Consequences: (1) re-embedding is an offline
batch job, never interactive; (2) the deploy must ship the built index - a
43-minute cold start is a dead demo; (3) query-side encoding of one short
query is a different (much smaller) cost and must be measured separately
for the p95 < 4 s budget.

## D7 — Fake encoder lesson + persist-before-metadata (2026-11-19)

First successful embedding run crashed after 42 minutes on
`model.name_or_path`: that attribute belongs to the underlying transformers
model, not the SentenceTransformer wrapper. The tests passed because the
FakeEncoder exposed the attribute - a test double more accommodating than
the real object hid the defect. Fix: label the model at load time and read
injected models with getattr(..., default). Two habits banked: (1) a fake
must mirror the real contract, or the code must not depend on unverified
attributes; (2) the builder persisted index and ids BEFORE building
metadata, so a metadata crash cost only metadata, not the compute -
persist expensive results before anything that can fail.
