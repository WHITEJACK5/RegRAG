# Retrieval metrics — definitions and interpretation

`regrag/eval/evalkit.py` implements four metrics and the paired bootstrap;
`regrag/eval/report.py` adds the pool-ceiling diagnostic.
`tests/test_evalkit.py` and `tests/test_eval_report.py` pin them with
hand-computed cases. This note is the stable reference for the ablation
tables and the README's evaluation section.

## Recall@k

Fraction of gold chunks present in the top-k:

    recall@k = |gold intersect top_k| / |gold|

- k = 6 because the prompt budget is top-6 (spec: rerank top-30 -> top-6).
- Multi-gold rows use the full denominator: G007 has 3 gold chunks, so
  finding 2 of 3 is 0.667, not 1.0.
- It ignores rank inside the top-k. A multi-hop answer that needs every
  gold chunk can still look partly successful. Read it with MRR and nDCG,
  and per question type.

## MRR

Mean reciprocal rank of the first gold hit:

    MRR = mean(1 / rank_of_first_hit)

- Rank 1 = 1.0; rank 3 = 0.333; no hit = 0.0.
- It ignores every hit after the first, so it under-rewards multi-gold
  questions. That is why nDCG exists.

## nDCG@k

Rank-weighted credit with binary relevance:

    DCG@k  = sum_{i=1..k} rel_i / log2(i + 1)
    IDCG@k = sum_{i=1..min(|gold|, k)} 1 / log2(i + 1)
    nDCG@k = DCG@k / IDCG@k

- A gold at rank 1 earns 1.0; the same gold at rank 5 earns
  1/log2(6) = 0.386.
- Binary relevance: a chunk is gold or it is not; we do not grade
  "partly relevant."
- IDCG puts all gold chunks first and normalises the scale to 0-1.

## Bootstrap CI

Percentile bootstrap for the mean of per-question scores:

- Resample the per-question values with replacement, 1000 times.
- Take the 2.5th and 97.5th percentiles of the resampled means.
- A fixed seed makes the interval deterministic: two runs on the same
  data agree.
- With 40 questions, a few points are noise. Report the interval; do not
  claim an ablation improvement when the intervals overlap.

## Paired bootstrap difference

Comparing two systems on the same questions is a paired design. Resample
question indices once per iteration and apply the same indices to both
systems; the interval is for `mean(a - b)`, not for either mean alone.

- Separate intervals can overlap while the paired difference is real,
  because the between-question variance cancels.
- `paired_bootstrap_diff(a, b)` returns the 95% interval for `mean(a - b)`;
  the caller reports the point estimate.
- D11 used it for the reranker: gain +0.026, CI [-0.052, +0.110] — no
  established improvement, which is one of the three reasons it was removed.

## Pool ceiling

`pool_ceiling(rows, pools, depth=30)` is the mean fraction of gold chunks
present in the candidate pool a reranker receives. It is the upper bound on
the reranker's Recall@6: reranking can only reorder what retrieval supplied.

- D11's ceiling was 1.000, so recall could improve (0.943 -> 0.974) only by
  moving gold from ranks 7–30 into the top 6.
- If the ceiling were below 1.0, recall would be capped there regardless of
  reranker quality.

## The empty-gold guard

Unanswerables have `gold_chunks = []` by design. They are scored by
refusal behaviour, not recall. Every metric raises `ValueError` on empty
gold instead of returning 0, so a scorer that forgets to filter
unanswerables fails loudly at the boundary.

## Worked example

gold = ["a"], retrieved = ["b", "c", "a"]:

- Recall@6 = 1.000 — "a" is in the top 6.
- MRR = 0.333 — first hit at rank 3.
- nDCG@6 = 0.500 — DCG = 1/log2(4); IDCG = 1/log2(2) = 1.
- Bootstrap CI on [0.0, 0.5, 1.0] is wide ([0.000, 1.000]) — with three
  values the interval is almost the whole range; this is why D10 reports
  intervals, not just means.
