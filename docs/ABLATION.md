# Retrieval ablation — dense vs BM25 vs RRF hybrid

First retrieval numbers for RegRAG, produced on D10 (Fri 20 Nov 2026) over the
40-question golden set. The 32 answerable rows are scored here; the 8
unanswerables have no gold chunks and are scored by refusal in D16.

## Setup

| item      | value                                                    |
| --------- | -------------------------------------------------------- |
| corpus    | 236 chunks, 5 documents (4 RBI + 1 synthetic)            |
| dense     | BGE-M3, 1024-d, L2-normalised, FAISS `IndexFlatIP`       |
| sparse    | `BM25Okapi`, identifier-preserving tokenizer             |
| fusion    | RRF, k=60, rank-only, ties by `chunk_id`                 |
| pool      | top 30 per retriever before fusion; final cut to 6       |
| metrics   | Recall@6, MRR, nDCG@6 (binary relevance)                 |
| intervals | percentile bootstrap, 1000 resamples, seed 0, 95%        |
| artifact  | `data/eval/retrieval_v1.json`                            |
| run       | `python scripts/score_retrieval.py`                      |
| timing    | 6.8 s model load, 9.7 s for 32 queries (CPU, warm cache) |

## Results

| slice    | system | n   | Recall@6             | MRR                  | nDCG@6               |
| -------- | ------ | --- | -------------------- | -------------------- | -------------------- |
| overall  | dense  | 32  | 0.917 [0.828, 0.984] | 0.673 [0.561, 0.786] | 0.717 [0.622, 0.816] |
| overall  | bm25   | 32  | 0.953 [0.875, 1.000] | 0.840 [0.740, 0.932] | 0.862 [0.774, 0.940] |
| overall  | hybrid | 32  | 0.943 [0.859, 1.000] | 0.839 [0.745, 0.922] | 0.846 [0.766, 0.918] |
| lookup   | dense  | 14  | 0.929 [0.786, 1.000] | 0.604 [0.417, 0.800] | 0.684 [0.518, 0.849] |
| lookup   | bm25   | 14  | 0.929 [0.786, 1.000] | 0.857 [0.679, 0.965] | 0.876 [0.707, 0.974] |
| lookup   | hybrid | 14  | 0.929 [0.786, 1.000] | 0.821 [0.643, 0.964] | 0.849 [0.688, 0.974] |
| multihop | dense  | 10  | 0.833 [0.667, 0.950] | 0.725 [0.550, 0.900] | 0.700 [0.552, 0.839] |
| multihop | bm25   | 10  | 0.950 [0.850, 1.000] | 0.820 [0.630, 1.000] | 0.834 [0.669, 0.957] |
| multihop | hybrid | 10  | 0.917 [0.800, 1.000] | 0.900 [0.800, 1.000] | 0.843 [0.714, 0.944] |
| numeric  | dense  | 8   | 1.000 [1.000, 1.000] | 0.729 [0.469, 0.917] | 0.795 [0.599, 0.938] |
| numeric  | bm25   | 8   | 1.000 [1.000, 1.000] | 0.833 [0.667, 1.000] | 0.875 [0.750, 1.000] |
| numeric  | hybrid | 8   | 1.000 [1.000, 1.000] | 0.792 [0.583, 0.938] | 0.845 [0.690, 0.954] |

## What the table says

1. **Recall@6 is high for every system** (0.917–0.953 overall), so at this
   depth the comparison is mostly about ordering, not about finding evidence.
2. **BM25 has the best top-rank point estimate overall** (MRR 0.840 vs dense
   0.673), and the largest gap is on lookup rows (0.857 vs 0.604). Dense finds
   the gold chunk (recall 0.929) but often places it at rank 3–6.
3. **Hybrid has the best multihop MRR point estimate** (0.900 vs 0.820 BM25,
   0.725 dense). Two-chunk questions reward two rankings: RRF promotes chunks
   both lists place well, and the 30-deep union carries both evidence chunks
   into the top 6.
4. **The numeric slice separates on ranking, not recall.** All three find 8/8
   gold chunks; MRR is 0.833 BM25 / 0.792 hybrid / 0.729 dense. That is
   consistent with the D8 tokenizer keeping section numbers and amounts whole.
5. **Dense's defect is ordering.** The lookup gap is the clearest target for
   the D11 cross-encoder, which re-reads query–chunk pairs instead of
   comparing two independent embeddings.

## Caveats — read before quoting any number

- **Builder-written questions.** The spec asked for five blind questions from
  a second person. No confirmed second person was available by D10, so all 40
  rows were written by the builder while reading the corpus. Question wording
  therefore overlaps regulation wording, which flatters lexical retrieval
  (BM25) relative to dense. The set is labelled builder-written in
  `docs/DECISIONS.md`.
- **No pairwise difference is separated by these intervals.** Each system's
  interval comes from its own bootstrap; every pair of intervals in the table
  overlaps. The point estimates are directional, not proof. A paired bootstrap
  over the same questions is the correct test for "A beats B" and is not yet
  implemented.
- **n = 32, and n = 8 on the numeric slice.** Intervals are wide by
  construction.
- **`1.000 [1.000, 1.000]` is degenerate, not certain.** The percentile
  bootstrap cannot invent variance when all eight values are 1.0. Recall@6
  cannot discriminate on that slice; MRR and nDCG are the informative columns.
- **Gold chunks are single-chunk annotations.** A neighbouring split chunk can
  repeat the same sentence and is still scored as a miss. This depresses MRR
  more than recall.

## Decision

Keep the hybrid pool for D11. The reranker survives only if the full pipeline
clears BM25's 0.840 overall MRR point estimate; if the gain sits inside the
noise, cut the reranker (first on the cut line) and report the BM25 baseline
with the same honesty. Blind questions, if they arrive before D19, are swapped
in while preserving the 14/10/8/8 mix, and this table is amended in a new
commit.

## Reproduce

```powershell
python scripts\score_retrieval.py
```
## File content — append to the end of `docs\DECISIONS.md`

One blank line after D9's last line, then:

```markdown
## D10 — Golden-set integrity: taxonomy, page 0, G008/G018 (2026-11-20)

Type is a property of the evidence required, not of how many rules an answer
mentions. `multihop` requires gold chunks from at least two distinct chunks; a
single chunk holding a rule and its exception is `lookup` (G018 reclassified).
G008 cited a page-28 table that duplicated c0034 under §5.9; it now cites
c0027 (§5.4). Guards added: `test_multihop_needs_two_chunks`,
`test_gold_page_is_covered_by_gold_chunks`, `test_gold_section_matches_a_gold_chunk`.
The synthetic policy has no printed page, so `pages: [0]` is the sentinel; the
presence check tests `is not None`, not truthiness. The earlier `if r["gold_page"]`
form silently skipped page 0. Lesson: zero is data, not absence.

## D10 — Aggregation lives in `regrag/eval/report.py` (2026-11-20)

The scorer does I/O: load BGE-M3, encode 32 queries, call three retrievers.
The report module does arithmetic: `score_rows`, `summarize`, `markdown`, all
pure and tested against a four-question toy set with hand-computed means. A
wrong mean is invisible in a plausible-looking table, and proving it right
must not require a 2 GB encoder. Same fake-encoder principle as D7. The run
persists `data/eval/retrieval_v1.json` and it is committed with the table, so
the numbers can be recomputed without re-encoding.

## D10 — First ablation: hybrid stays, BM25 is the bar (2026-11-20)

On 32 answerable rows all systems reach 0.917–0.953 Recall@6. BM25 has the best
overall MRR point estimate (0.840) against dense 0.673 and hybrid 0.839; hybrid
is best on multihop MRR (0.900 vs 0.820 and 0.725). Dense finds lookup evidence
(0.929 recall) but orders it poorly (0.604 MRR) — an ordering gap, which is what
a cross-encoder addresses. Every pair of 95% intervals overlaps, so none of
these differences is established at n=32. Decision: keep the hybrid pool for
D11; the reranker must clear BM25's 0.840 overall MRR point estimate or be cut.

## D10 — The 40 questions are builder-written (2026-11-20)

The spec asks for five blind questions from a second person. No confirmed
second person was available by D10, so all 40 rows were written by the builder
while reading the corpus. Consequence: lexical overlap between question and
regulation wording flatters BM25, and the ablation table must say so. The table
in `docs/ABLATION.md` is labelled builder-written. Upgrade path: if a blind set
exists before D19, swap it in while preserving the 14/10/8/8 mix, re-score, and
amend the table, README and this log in a new commit. The set is never
presented as blind.