"""Verify the manuscript's citations, frozen results table, and compiled artifact."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import bibtexparser
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper'
subprocess.run([sys.executable, str(PAPER / 'verify_evidence.py')], check=True)
source = (PAPER / 'manuscript/main.tex').read_text()
occurrences = re.findall(r'\\evidencecite\{(C\d{2})\}\{([^}]+)\}\{([^}]+)\}', source)
sources = json.loads((PAPER / 'evidence/sources.json').read_text())
expected = []
for entry in sorted(sources, key=lambda x: x['planned_reference_number']):
    bib = bibtexparser.parse_string((PAPER / 'evidence' / f'{entry["source_id"]}-publisher.bib').read_text())
    expected.append((entry['occurrence_id'], bib.entries[0].key))
expected.append(('C11', 'taco-dataset'))
assert [(occ, key) for occ, key, _ in occurrences] == expected
record = json.loads((PAPER / 'manuscript/build-record.json').read_text())
for path, sha in record['inputs'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
pdf_path = ROOT / record['pdf']
assert hashlib.sha256(pdf_path.read_bytes()).hexdigest() == record['pdf_sha256']
pdf = pymupdf.open(pdf_path)
main_pages = next(i for i, page in enumerate(pdf) if 'APPENDIX: CITATION EVIDENCE' in page.get_text())
assert 3 <= main_pages <= 6
assert len(pdf) == main_pages + 12
text = '\n'.join(page.get_text() for page in pdf[:main_pages])
assert '??' not in text
assert '13,068' in text and '72/72' in text
assert 'AI ASSISTANCE AND REPRODUCIBILITY' in text
for entry, page in zip(sources, pdf[main_pages + 1:main_pages + 11]):
    assert f'[{entry["planned_reference_number"]}] {entry["occurrence_id"]} / {entry["source_id"]}' in page.get_text()
assert '[11] C11 / S11' in pdf[-1].get_text()
dataset = json.loads((PAPER / 'evidence/dataset-record.json').read_text())
assert hashlib.sha256((PAPER / 'evidence/C11-S11-dataset-card.png').read_bytes()).hexdigest() == dataset['screenshot_sha256']
assert hashlib.sha256((PAPER / 'evidence/dataset-evidence.pdf').read_bytes()).hexdigest() == dataset['evidence_pdf_sha256']
analysis = json.loads((ROOT / 'studies/format-study1/results/analysis.json').read_text())
table = (PAPER / 'manuscript/results-table.tex').read_text()
for task in analysis['per_task']:
    tid = task['task_id']
    directory = ROOT / 'studies/format-study1/source/selected' / tid
    cases = json.loads((directory / 'evaluation-cases.json').read_text())
    label = json.loads((directory / 'task.json').read_text())['difficulty'][0]
    assert f"{tid[-4:]} & {label} & {len(cases['inputs'])} & 2/2 & 2/2 & 2/2" in table
build = ROOT / 'work/paper-build'
if (build / 'main.aux').exists():
    tags = dict(re.findall(r'\\bibcite\{([^}]+)\}\{(\d+)\}', (build / 'main.aux').read_text()))
    assert [tags[key] for _, key in expected] == [str(i) for i in range(1, 12)]
    log = (build / 'main.log').read_text()
    assert not re.search(r'Overfull \\hbox|LaTeX Warning: (?:Citation|Reference).*undefined|^! ', log, re.M)
    assert hashlib.sha256((build / 'main.log').read_bytes()).hexdigest() == record['tex_log_sha256']
print(f'PASS: {main_pages} main pages, {len(pdf)} total pages, 11 mapped citations, 12 matching task rows')
