"""Check citation evidence coverage without contacting publishers."""
import hashlib
import json
from pathlib import Path
import re

import pymupdf
import bibtexparser

ROOT = Path(__file__).resolve().parent
sources = json.loads((ROOT / 'evidence/sources.json').read_text())
render = json.loads((ROOT / 'evidence/render-manifest.json').read_text())
assert len(sources) == len(render['sources']) == 10
assert len({s['source_id'] for s in sources}) == 10
assert len({s['planned_reference_number'] for s in sources}) == 10
occurrences = re.findall(r'\*\*(C\d{2}) → (S\d{2})\*\*', (ROOT / 'outline.md').read_text())
assert sorted(occurrences) == sorted((s['occurrence_id'], s['source_id']) for s in sources)
assert [sid for _, sid in occurrences] == [s['source_id'] for s in sorted(sources, key=lambda s: s['planned_reference_number'])]
for source, rendered in zip(sources, render['sources']):
    assert source['source_id'] == rendered['source_id']
    assert source['occurrence_id'] == rendered['occurrence_id']
    path = ROOT / rendered['screenshot']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == rendered['screenshot_sha256']
    assert rendered['highlight_quads']
    assert len(pymupdf.Pixmap(path).samples) > 0
    cached = ROOT.parent / 'work/paper-sources' / f'{source["source_id"]}.pdf'
    if cached.exists():
        assert hashlib.sha256(cached.read_bytes()).hexdigest() == source['source_pdf_sha256']
        doc = pymupdf.open(cached)
        for excerpt in source['highlight_excerpts']:
            assert doc[source['pdf_page'] - 1].search_for(excerpt)
appendix = ROOT / 'output/citation-appendix.pdf'
assert hashlib.sha256(appendix.read_bytes()).hexdigest() == render['appendix_sha256']
pages = pymupdf.open(appendix)
assert len(pages) == 10
for source, page in zip(sources, pages):
    assert f'[{source["planned_reference_number"]}] {source["occurrence_id"]} / {source["source_id"]}' in page.get_text()
assert len(re.findall(r'@inproceedings\s*\{', (ROOT / 'references.bib').read_text(), re.I)) == 10
bibliography = bibtexparser.parse_string((ROOT / 'references.bib').read_text())
assert len(bibliography.entries) == 10 and not bibliography.failed_blocks
for entry in bibliography.entries:
    assert all(key in entry.fields_dict for key in ['title', 'author', 'booktitle', 'year'])
print('PASS: 10 sources, 10 citation occurrences, 10 intact screenshots, 10 appendix pages')
