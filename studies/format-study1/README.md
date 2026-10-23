# Independent prompt-format study: completed

This study fixed twelve externally authored programming problems, three equivalent presentation formats, and two fresh responses per task/format. **All 72 responses were collected and all 72 passed their retained task suites.** It requested **`gpt-6.1-sol` with `medium` reasoning**, matching the earlier pilots. The reported model alias matched the request. It is a separate study, `format-study1`; the earlier pilot-3 no-launch decision is unchanged.

Read the [protocol](PROTOCOL.md), [preparation verification](verification.md), [collected findings](results/findings.md), [run verification](results/verification.md), and [source provenance and attribution](NOTICE.md). The freeze covers source records, original and curated tests, references, prompts, allocation, analysis, grader, and isolation controls. A synthetic live backend canary passed before collection; its record is under `runs/`.

## Task pool and frozen tests

The pinned [TACO source](source/ACQUISITION.md) supplies external competition statements and reference programs. Selection uses a deterministic ranking and six MEDIUM plus six HARD source labels, without target-model calibration. Those labels do not guarantee difficulty for this model.

The original 2,339 source cases remain unchanged. Statement-derived validators retain **2,178 cases**; all **161 exclusions** have indices, constraint/shape reasons, and original hashes. Retained input and expected-output strings are unchanged. The export retains every case passing the validators, regardless of reference outcomes. Supplied references pass all 2,178 retained cases in the restricted grader, with the documented infrastructure recovery below. This is a **curated subset experiment, not an official TACO score**.

| Source row | Label | Problem | Original cases | Retained cases |
|---|---|---|---:|---:|
| 0760 | MEDIUM | Minimum-product index triples | 334 | 334 |
| 0402 | MEDIUM | Rooted-tree consecutive-cat paths | 196 | 179 |
| 0472 | MEDIUM | Four chessboard pieces | 164 | 160 |
| 0074 | MEDIUM | Stack reorder commands | 180 | 143 |
| 0250 | MEDIUM | Lucky multipliers and trailing zeros | 278 | 254 |
| 0320 | MEDIUM | Power-of-two grouping | 238 | 237 |
| 0799 | HARD | Subarray counts by values below a threshold | 51 | 50 |
| 0339 | HARD | Weighted sorted subarray sums | 242 | 225 |
| 0466 | HARD | Prefix XOR with point updates | 157 | 135 |
| 0581 | HARD | Tree vertex deletion and component GCD | 206 | 205 |
| 0152 | HARD | Bottleneck bipartite matching | 49 | 18 |
| 0979 | HARD | Binary-substring range queries | 244 | 238 |

The preparation audit also found damaged statements and contradictory or malformed fixtures in an earlier selection. [Initial selection](source/initial-selection.json), [defect witnesses](source/preparation-defects.json), excluded originals, and superseded reference evidence preserve those decisions. The curated policy was explicitly amended before any target-model response. A retained table-game case also had a semantically wrong expected answer, independently proved from the rules. The entire task 0778 was replaced by the next eligible HARD task, 0799, before any target-model generation. The [semantic-defect proof](source/semantic-defect-0778.json) and [superseded validation](superseded-preflight-v1/reference-validation.json) preserve this amendment. No expected values were repaired to make references pass.

## Treatment and collection boundary

A renders the canonical blocks as prose, B as a numbered list, and C as XML. All 36 prompts reconstruct the same question and contain identical implementation/output requirements. The 72-row [schedule](trials.json) balances all six format orders four times, with seed `20261022`. This seed controls allocation only.

Each candidate ran in a fresh container without host mounts, references, tests, previous answers, credentials, execution tools, or direct internet access. The real pinned Codex client was exercised offline against a synthetic provider before the live canary; the captured request used the requested model, medium reasoning, and `tools: []`. The relay controlled the sole provider route. Read the [isolation controls and live gate](isolation/README.md).

The primary outcome is passing every retained test under the frozen grader. All 72 responses were evaluable and passed, giving 13,068/13,068 successful case checks. A, B, and C each scored 24/24 all-case passes. Both prespecified equal-task mean contrasts, B−A and C−A, were zero. There is no significance test, equivalence claim, or post-result task replacement.

## Verify the preparation

From the repository root, with Python and Docker available:

```sh
python3 studies/format-study1/prepare.py verify
python3 -m unittest discover -s studies/format-study1/tests -v
python3 -m unittest discover -s studies/format-study1/source -p test_validators.py -v
python3 -m unittest discover -s studies/format-study1/isolation -p 'test_*.py' -v
node studies/format-study1/isolation/test_live_transport.mjs
```

These checks do not call an inference provider. The saved [reference report](reference-validation.json) and [first-attempt per-case log](reference-validation.cases.jsonl) provide the pre-freeze Docker execution evidence. A Docker cleanup interruption on task 0320 triggered a separately logged [full-task recovery](reference-recovery.cases.jsonl), with the failed attempt retained in `reference-attempts/attempt-1/`. The final report links the contributing attempts explicitly. Reproducing acquisition, export, build, or reference validation must use a separate unfrozen copy; do not overwrite this freeze. See [acquisition instructions](source/ACQUISITION.md).

## What the completed study can support

The design improves external task authorship, prompt-content equivalence, test provenance, allocation, and reference isolation. It gives a complete observation of **no detected correctness difference** among the three formats on these frozen suites. Because every format reached the endpoint ceiling, it gives little information about correctness sensitivity on tasks where failures are possible.

The external tests are mostly small. Task 0339 reaches n=30 against a statement limit of 500,000; task 0760 reaches n=20 against 100,000. Inefficient programs may pass, and another ceiling remains possible. The endpoint is finite-suite correctness, not full contest acceptance or algorithmic efficiency. The public problems may also have appeared in model training. Twelve filtered tasks and two repetitions per format support an exploratory result, not a broad claim about model robustness.

The synthetic live canary passed with the requested alias and medium reasoning. No fallback was used. Provider-reported identity is not independent attestation of provider internals. The [saved collection and analysis](results/findings.md) preserve the completed result.
