# Retrieval metrics — definitions and interpretation

`regrag/eval/evalkit.py` implements four metrics; `tests/test_evalkit.py`
pins the definitions with hand-computed cases. This note is the stable
reference for D10's ablation table and the README's evaluation section.

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
