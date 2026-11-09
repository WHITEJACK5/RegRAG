# Corpus — design notes

What the RegRAG corpus is, why each member is in it, and the rules that keep
every later citation honest.

## Members

1. **Four public RBI documents** (URLs, SHA-256 checksums, effective dates and
   statuses live in `data/MANIFEST.json`):
   - `rbi_digital_lending_2025` — RBI (Digital Lending) Directions, 2025.
     Consolidates and repeals the 2022 digital-lending guidelines, so the
     superseded 2022 text is deliberately NOT in the corpus.
   - `rbi_kyc_2016` — Master Direction — KYC Direction, 2016, consolidated
     text updated as on 2025-08-14 (we keep the update, not the original).
   - `rbi_iracp_2025` — Master Circular — prudential norms on IRACP for
     advances (reissued each April; status re-checked before relying on it).
   - `rbi_fair_practices_code` — Master Circular — Fair Practices Code
     (operative consolidated text; the 2024-04-29 charging-of-interest
     circular sits on top of it — recorded in its MANIFEST status).
2. **`data/synthetic_policy_v1.md`** — the internal policy of the fictional
   "SahiCredit Finance Pvt Ltd" (labelled SYNTHETIC in the file itself), to be
   converted to a clearly-labelled PDF at parse time (D3+).

## Why it is built this way

- Every policy rule is tagged `[trace: <rbi doc_id>]`, `[internal]`, or
  `VERIFY-D3` (not yet verified against a parsed RBI paragraph — must not be
  cited by any answer until D3 hand-checks confirm it). This traceability is
  what makes later multi-hop questions honest ("Does our 40% LTI cap comply
  with the direction on X?").
- PDFs are never committed to git; `MANIFEST.json` is the tracked record.
- Nothing in the corpus contains personal data or real contacts (the
  fictional lender uses the reserved `.example` domain).

## Re-verification habit

RBI reissues documents (the IRACP Master Circular every April). Before
relying on any item: re-read MANIFEST `status` + `effective_date`, re-run
`python scripts/download_data.py` (idempotent), and run
`python scripts/corpus_inventory.py` for a one-pass summary.
