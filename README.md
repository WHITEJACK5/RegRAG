# RegRAG

Citation-grounded question answering over Indian retail-lending regulation
(RBI Master Directions / circulars) and a synthetic internal lending policy.

**Claim:** every answer carries page-level citations with a verbatim quote that
code verifies; when the corpus does not support an answer, the system refuses.

**Status:** early build (D1 of 20 · 9 Nov – 6 Dec 2026). Full README with
results, evaluation and ablation tables lands at the end of the build window.

- Educational project. Not legal or financial advice.
- Public RBI documents; PDFs are never committed to git (see `MANIFEST.json`
  for checksums and effective dates).

5. PROJECT_RULES.md (root)

# Project Rules — RegRAG

Source of truth: the RegRAG Project Specification + Project Guide
("the ramayana"): Downloads/PLAN_90D/PROJECTS/REGRAG_SPEC.html and
"RegRAG — Project Guide.docx". Build dir: Downloads/KAAAAM/ai_project/REGRAG.

## Daily commit protocol

- Every working day ends with **exactly 9 commits** (no more, no fewer),
  regardless of how much or how little was done.
- Commits are made as a batch at end of day, sliced into logical units
  (setup / code / tests / docs), with clear messages, then pushed.

## Hard rules (from the spec)

- Secrets never in git: `.env` is ignored; only `.env.example` is committed.
- PDFs never committed to git; `data/MANIFEST.json` records source + SHA-256.
- Never cut: citation validator, unanswerable golden questions, injection suite.
- Cost: Gemini free tier for now; spend cap set in .env before D12 generation.

## Working format

- One dev (WHITEJACK5) + AI tutor (opencode). Commands run by the dev; AI reads
  real outputs before every next step. Learning is a deliverable, not a side effect.
