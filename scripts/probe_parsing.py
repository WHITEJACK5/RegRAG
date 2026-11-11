"""D3 probe - look at the raw material before writing the parser.

No parsing logic here. Three questions only:
  1. What does extract_text() actually give us for page 1?
  2. How many pages does the document claim?
  3. What do tables look like when pdfplumber tries?

Run:  python scripts/probe_parsing.py
"""

from pathlib import Path

import pdfplumber

PDF = Path(__file__).resolve().parent.parent / "data" / "rbi_fair_practices_code.pdf"


def main() -> int:
    if not PDF.exists():
        print(f"missing: {PDF}")
        return 1

    with pdfplumber.open(PDF) as pdf:
        print(f"pages in file: {len(pdf.pages)}")
        print(f"document metadata: {pdf.metadata}")  # sometimes has title/date

        page = pdf.pages[0]
        print("\n--- extract_text(), page 1, first 1200 chars ---")
        text = page.extract_text() or ""
        print(text[:1200] or "(empty - no text layer on this page)")

        print("\n--- table attempts, first 3 pages ---")
        for i, p in enumerate(pdf.pages[:3], start=1):
            tables = p.extract_tables()
            print(f"page {i}: {len(tables)} table(s)")
            for t in tables:
                rows = [[(c or "")[:18] for c in row] for row in t[:4]]
                for r in rows:
                    print("   |", r)

        print("\n--- character-level sample (provenance granularity) ---")
        for ch in page.chars[:5]:
            print(f"   {ch['text']!r}  page={page.page_number}  "
                  f"x={ch['x0']:.1f} y={ch['top']:.1f} font={ch['fontname']} size={ch['size']:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())