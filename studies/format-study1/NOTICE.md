# TACO external task provenance

The source files and preparation records named below are in [`source/`](source/).

Task statements, supplied input/output tests, supplied solution programs, source names, URLs, and difficulty labels are external material from BAAI/TACO. These tasks were authored independently of this experiment. The acquisition script, selection policy, format adapters, and experiment protocol are AI-assisted experiment materials. Supplied solutions are external references, not newly authored oracle implementations.

Dataset source: https://huggingface.co/datasets/BAAI/TACO/tree/d593ed0a2becbbc952230bb89be09189bf1056dc

Pinned dataset revision: `d593ed0a2becbbc952230bb89be09189bf1056dc`. The pinned dataset card declares Apache-2.0 for the authored dataset, and explicitly states that incorporated material also carries MIT or CC BY 4.0. HackerRank material has unknown rights and is excluded from this selection. The original source acknowledgments and citation are retained in README.upstream.md. CC BY 4.0 terms are retained in LICENSE-CC-BY-4.0.txt. The official project links that dataset and carries the retained Apache-2.0 `LICENSE`. TACO aggregates competition material, so the dataset-level declaration should not be mistaken for a separate investigation of every original contest website's terms. Original task URLs and source fields are preserved in each selected record.

Official project: https://github.com/FlagOpen/TACO

Project metadata and special-judge exclusion list are pinned to `245eba3beb2d23a07082307de303de2589e4321a`. `README.github.md`, `README.upstream.md`, `LICENSE`, and `output_spj.jsonl` are retained. The exclusion list is indexed by the official test-set row index. Selection also independently excludes HackerRank material, function tasks, interactive wording, flexible-output wording, and floating point output literals.

The original Parquet is read as data using PyArrow. No remote dataset loading code, pickle deserialization, reference execution, or model trial is used during acquisition. `select.py` only parses solution ASTs. Reference correctness and output compatibility remain provisional until every selected supplied solution passes every curated evaluation case inside the experiment container. No reference program has been executed on the host.

Selection is fixed before target-model outcomes. Seed `scm-format-study1-external-v1` ranks eligible external IDs with SHA-256. Six externally labeled MEDIUM tasks and six HARD tasks are selected. Static eligibility is not a guarantee of Python runtime compatibility or unique-output semantics. No replacements may be chosen based on target-model performance.

Preparation history is retained in `initial-selection.json`, `initial-select.py`, and `preparation-defects.json`. Missing-image statements, contradictory duplicate fixtures, and independently confirmed malformed cases were excluded before any model generation. The seed and rank order are unchanged.

The first curated snapshot used 2,318 of 2,483 original cases and documented 165 structural exclusions. That historical snapshot is preserved unchanged before the semantic whole-task replacement described below. The retained subset is not an official TACO benchmark evaluation. `evaluation-index-map.json` binds original indices and subset hashes.

Before freeze, independent statement-only review proved row 778 case 94 semantically incorrect. The entire task was replaced by next-ranked HARD row 799. The previous complete selection and its evaluation map are preserved in `pre-semantic-replacement/`; the rejected originals remain in `excluded/taco-test-0778/`. The final candidate set retains 2,178 of 2,339 original cases and records 161 structural exclusions. No expected outputs were repaired.

For row 799 original case 25, the input is valid. The supplied expected output has six integers although n=6 requires seven. The frozen generic parser message `Input truncated` arises while reading expected-output tokens, not input. `case-0799-25-provenance-correction.json` records the precise reason without changing validators, evaluation files, or retained indices.
