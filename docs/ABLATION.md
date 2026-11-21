File content — replace all of docs\ABLATION.md

# Retrieval ablation — dense vs BM25 vs RRF hybrid, and the reranker

First retrieval numbers for RegRAG, produced on D10 (Fri 20 Nov 2026) over the
40-question golden set. D11 (Sat 21 Nov 2026) adds the cross-encoder experiment.
The 32 answerable rows are scored here; the 8 unanswerables have no gold chunks
and are scored by refusal in D16.

## Setup

| item      | value                                                                      |
| --------- | -------------------------------------------------------------------------- |
| corpus    | 236 chunks, 5 documents (4 RBI + 1 synthetic)                              |
| dense     | BGE-M3, 1024-d, L2-normalised, FAISS `IndexFlatIP`                         |
| sparse    | `BM25Okapi`, identifier-preserving tokenizer                               |
| fusion    | RRF, k=60, rank-only, ties by `chunk_id`                                   |
| reranker  | `BAAI/bge-reranker-base`, query-chunk pairs, 512 tokens, CPU               |
| pool      | top 30 per retriever before fusion; the reranker consumes the fused top 30 |
| metrics   | Recall@6, MRR, nDCG@6 (binary relevance)                                   |
| intervals | percentile bootstrap, 1000 resamples, seed 0, 95%                          |
| artifacts | `data/eval/retrieval_v1.json`, `data/eval/rerank_v1.json`                  |
| runs      | `python scripts/score_retrieval.py`, `python scripts/score_rerank.py`      |

## Results — retrievers (D10)

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

## What the D10 table says

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
5. **Dense's defect is ordering.** The lookup gap was the target for the D11
   cross-encoder. D11 improved lookup sharply but regressed multihop and lost
   on latency; see below.

## Results — reranker (D11)

| slice    | system        | n   | Recall@6             | MRR                  | nDCG@6               |
| -------- | ------------- | --- | -------------------- | -------------------- | -------------------- |
| overall  | hybrid        | 32  | 0.943 [0.859, 1.000] | 0.839 [0.745, 0.922] | 0.846 [0.766, 0.918] |
| overall  | hybrid_rerank | 32  | 0.974 [0.938, 1.000] | 0.865 [0.760, 0.948] | 0.873 [0.796, 0.940] |
| lookup   | hybrid        | 14  | 0.929 [0.786, 1.000] | 0.821 [0.643, 0.964] | 0.849 [0.688, 0.974] |
| lookup   | hybrid_rerank | 14  | 1.000 [1.000, 1.000] | 0.905 [0.750, 1.000] | 0.928 [0.809, 1.000] |
| multihop | hybrid        | 10  | 0.917 [0.800, 1.000] | 0.900 [0.800, 1.000] | 0.843 [0.714, 0.944] |
| multihop | hybrid_rerank | 10  | 0.917 [0.800, 1.000] | 0.867 [0.683, 1.000] | 0.820 [0.668, 0.927] |
| numeric  | hybrid        | 8   | 1.000 [1.000, 1.000] | 0.792 [0.583, 0.938] | 0.845 [0.690, 0.954] |
| numeric  | hybrid_rerank | 8   | 1.000 [1.000, 1.000] | 0.792 [0.604, 0.938] | 0.845 [0.707, 0.954] |

Latency over 32 queries: mean **50.7 s**, p50 47.1 s, p95 **68.3 s**, max
71.6 s, **0.59 pairs/s**, 1621 s total; model load 6.6 s from cache. Pool
ceiling (Recall@30 of the hybrid pool): **1.000**. Paired MRR gain
(rerank − hybrid): **+0.026**, 95% CI **[-0.052, +0.110]**.

## What the reranker table says

1. **Lookup is where it works.** Recall 0.929 → 1.000; MRR 0.821 → 0.905;
   nDCG 0.849 → 0.928. With one gold chunk per question, a pair scorer can
   promote the right chunk from rank 3–6 to rank 1.
2. **Multihop regresses.** MRR 0.900 → 0.867; nDCG 0.843 → 0.820; recall is
   unchanged at 0.917. A cross-encoder scores each chunk against the query
   independently, so it cannot reward two chunks that are jointly sufficient.
   Promoting one can push its partner out of the top 6.
3. **Numeric is unchanged.** Both systems already have 1.000 recall; MRR stays
   0.792 and nDCG 0.845. The reranker did not disturb an already-correct order.
4. **The overall gain is inside the noise.** +0.026 MRR is below the
   pre-registered 0.03 bar, and the paired 95% CI includes zero. The lookup
   gain is real in direction but diluted by the multihop regression.
5. **The cost is decisive.** p95 68.3 s/query is ~68× the 1.0 s budget. Even a
   perfect quality gain would not justify it on this CPU.

## Caveats — read before quoting any number

- **Builder-written questions.** The spec asked for five blind questions from
  a second person. No confirmed second person was available by D10, so all 40
  rows were written by the builder while reading the corpus. Question wording
  therefore overlaps regulation wording, which flatters lexical retrieval
  (BM25) relative to dense. The set is labelled builder-written in
  `docs/DECISIONS.md`.
- **D10 intervals are separate; D11 is paired.** Overlapping separate intervals
  do not mean "no difference": they include between-question variance that
  cancels in a paired design. The D11 comparison uses `paired_bootstrap_diff`
  over the same 32 questions; that is the correct test for a difference.
- **n = 32, and n = 8 on the numeric slice.** Intervals are wide by
  construction.
- **`1.000 [1.000, 1.000]` is degenerate, not certain.** The percentile
  bootstrap cannot invent variance when all eight values are 1.0. Recall@6
  cannot discriminate on that slice; MRR and nDCG are the informative columns.
- **Gold chunks are single-chunk annotations.** A neighbouring split chunk can
  repeat the same sentence and is still scored as a miss. This depresses MRR
  more than recall.
- **Raw chunk text.** The reranker sees PDF footer artifacts and 512-token
  truncation. Cleaning the text could change the ordering, but would not change
  the latency verdict.
- **One model, one hardware profile.** `bge-reranker-base` on this 12-thread
  CPU. A GPU or a much smaller model could change the trade-off; the decision
  is for this deployment target, not a universal claim.

## Decision

Keep hybrid. Remove the reranker from the serving path: three independent
failures of the pre-registered rule (gain < 0.03, paired CI includes zero,
p95 68.3 s > 1.0 s). The code and artifact stay in the repo as an experiment;
D12+ uses hybrid top-6 without reranking. If the deployment hardware changes
enough to cut latency by ~68×, re-run `score_rerank.py` and re-apply the same
rule.

## Reproduce

```powershell
python scripts\score_retrieval.py
python scripts\score_rerank.py
```
