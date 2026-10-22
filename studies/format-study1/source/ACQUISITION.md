# Reproduce the external task selection

The source shard is 245,784,461 bytes. It remains outside the committed study. `acquire.py` downloads only the pinned Parquet and verifies its SHA-256. It does not execute dataset-loading code.

The recorded acquisition used Python 3.14.7 and PyArrow 26.0.0. Run these commands from the repository root.

```sh
python3 -m venv work/poteto/independent/source/venv
work/poteto/independent/source/venv/bin/pip install pyarrow==26.0.0
python3 studies/format-study1/source/acquire.py work/poteto/independent/source/test.parquet
work/poteto/independent/source/venv/bin/python studies/format-study1/source/select.py --dataset work/poteto/independent/source/test.parquet --output-dir studies/format-study1/source
python3 studies/format-study1/source/validate_selected.py --export
python3 -m unittest discover -s studies/format-study1/source -p test_validators.py -v
```

`select.py` emits the eligible census, exclusion records with original-row hashes, supplied-reference hashes, deterministic ranking, and selected task files. It parses Python ASTs but never executes supplied programs. The task selection uses six MEDIUM and six HARD tasks, ranked with the fixed seed before any target-model generation.

Preparation added two generic gates across the pool. Statements containing `<image>` are excluded. Duplicate inputs after CRLF and surrounding-whitespace normalization must have identical expected outputs after whitespace-token normalization. Independently confirmed malformed source fixtures caused whole-task exclusions. `initial-selection.json`, `initial-select.py`, and preparation history retain those decisions and witnesses. After independent review disproved a valid-case expected output in row 778, that whole task was replaced by next-ranked HARD row 799 before freeze. The previous complete selection and validation hashes are preserved in `pre-semantic-replacement/`. The external seed and rank remain unchanged.

The source contains mutated tests that violate original statements. The curated evaluation therefore retains every original case accepted by independent statement-derived input, domain, and expected-output-shape validators. These checks do not compute answers or observe reference/model pass rates. The original 2,339 cases remain unchanged in `selected/*/task.json`. Each sibling `evaluation-cases.json` retains unchanged input and expected strings for the 2,178 accepted cases, original case indices, and all 161 excluded-case reasons and hashes. Every task retains at least 18 cases.

`validate_selected.py --export` deterministically regenerates the subset and `evaluation-index-map.json`. The structural report includes raw and curated counts, exact source and evaluation hashes, and validator hashes. `test_validators.py` checks valid examples, specific domain rejections, trailing input/output rejection for all twelve task contracts, and exact original-to-curated subset identity.

Every retained case must pass an independently supplied reference inside the experiment container before freeze. A retained-case disagreement requires diagnosis of supplied references or fixture ambiguity. A valid case cannot be removed because a reference fails. No expected output or original reference is repaired. This curated experiment is not an official or directly comparable TACO benchmark score.
