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
