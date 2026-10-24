#!/usr/bin/env python3
"""Check the compiled note's citations, references, and page count."""

from __future__ import annotations

import re
from pathlib import Path


tex = Path("note.tex").read_text()
bib = Path("refs.bib").read_text()
log = Path("note.log").read_text()
cited = {
    key.strip()
    for citation in re.findall(r"\\cite[pt]\{([^}]+)\}", tex)
    for key in citation.split(",")
}
defined = set(re.findall(r"@\w+\s*\{([^,]+),", bib))
assert cited <= defined, f"Undefined citation keys: {cited - defined}"
assert defined <= cited, f"Uncited bibliography entries: {defined - cited}"
match = re.search(r"Output written on note\.pdf \((\d+) pages", log)
assert match, "Could not read page count from note.log"
print(f"Citation keys verified: {len(cited)}")
print(f"PDF page count: {match.group(1)}")
