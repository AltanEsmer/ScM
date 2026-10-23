"""Compile the IEEE draft and record the source-to-PDF bindings."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tectonic', default='tectonic')
args = parser.parse_args()
analysis = json.loads((ROOT / 'studies/format-study1/results/analysis.json').read_text())
assert len(analysis['per_task']) == 12
assert all(task['cells'][v]['successes'] == task['cells'][v]['evaluable'] == 2 for task in analysis['per_task'] for v in 'ABC')
rows = [r'\begin{table}[t]', r'\caption{All-case successes by task and format. M and H are the dataset difficulty labels. Cases are retained fixtures per program.}', r'\label{tab:results}', r'\centering', r'\small', r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule', r'Task & Label & Cases & A & B & C\\', r'\midrule']
fixture_total = 0
for task in analysis['per_task']:
    tid = task['task_id']
    task_dir = ROOT / 'studies/format-study1/source/selected' / tid
    source = json.loads((task_dir / 'task.json').read_text())
    cases = json.loads((task_dir / 'evaluation-cases.json').read_text())
    fixture_total += len(cases['inputs'])
    cells = [f"{task['cells'][v]['successes']}/{task['cells'][v]['evaluable']}" for v in 'ABC']
    rows.append(' & '.join([tid[-4:], source['difficulty'][0], str(len(cases['inputs'])), *cells]) + r'\\')
assert fixture_total == 2178
assert analysis['complete'] and analysis['scheduled_trials'] == 72
rows.extend([r'\midrule', r'Total & & 2,178 & 24/24 & 24/24 & 24/24\\', r'\bottomrule', r'\end{tabular}', r'\end{table}'])
(PAPER / 'manuscript/results-table.tex').write_text('\n'.join(rows) + '\n')
build = ROOT / 'work/paper-build'
build.mkdir(parents=True, exist_ok=True)
compiler = shutil.which(args.tectonic)
if compiler is None:
    raise SystemExit('Tectonic is required. Install it or pass --tectonic /path/to/tectonic.')
version = subprocess.check_output([compiler, '--version'], text=True).strip()
command = [compiler, '--keep-logs', '--keep-intermediates', '--outdir', str(build), 'main.tex']
result = subprocess.run(command, cwd=PAPER / 'manuscript', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(build / 'build.log').write_text(result.stdout)
if result.returncode:
    raise SystemExit(result.stdout)
output = PAPER / 'output/preliminary-paper.pdf'
shutil.copyfile(build / 'main.pdf', output)
inputs = ['paper/manuscript/main.tex', 'paper/manuscript/results-table.tex', 'paper/references.bib', 'paper/manuscript/additional-references.bib', 'paper/output/citation-appendix.pdf', 'paper/evidence/dataset-evidence.pdf', 'paper/evidence/dataset-record.json', 'studies/format-study1/results/analysis.json']
record = {'compiler': version, 'document_class': 'IEEEtran conference, A4, 10pt, two columns', 'inputs': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs}, 'pdf': str(output.relative_to(ROOT)), 'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'tex_log_sha256': hashlib.sha256((build / 'main.log').read_bytes()).hexdigest()}
(PAPER / 'manuscript/build-record.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'{version}: compiled {output}')
