"""D2: file-level corpus integrity, checked against the manifest.

The D1 smoke tests validated the DOCS *list*; these validate the actual
*files on disk*: present, real PDFs (magic bytes), and dates well-formed.
No network access - this works offline, before any download.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _manifest() -> dict:
    p = DATA / "MANIFEST.json"
    assert p.exists(), "MANIFEST.json missing - run scripts/download_data.py first"
    return json.loads(p.read_text(encoding="utf-8"))


def test_every_manifest_file_is_present_and_real_pdf():
    for d in _manifest()["docs"]:
        f = DATA / d["file"]
        assert f.exists(), f"{d['file']} missing on disk"
        with f.open("rb") as fh:
            assert fh.read(5) == b"%PDF-", f"{d['file']} is not a real PDF"


def test_manifest_dates_are_iso():
    for d in _manifest()["docs"]:
        date = d["effective_date"]
        assert len(date) == 10 and date[4] == "-" and date[7] == "-"


def test_manifest_checksums_are_64_hex():
    for d in _manifest()["docs"]:
        assert len(d["sha256"]) == 64
        int(d["sha256"], 16)  # raises if not hex
