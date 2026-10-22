# Audit saved composite answers with stronger tests

This post-hoc robustness audit applies new tests to the 30 saved responses from composite calibration round 2. It collects no new responses and changes no original prompts, tests, records, grading code, results, or pilot-3 selection decision. The requested model and reasoning setting of the saved sample remain `gpt-6.1-sol`, medium.

The audit asks whether broader tests expose errors that the original finite tests missed. It cannot estimate prompt sensitivity because the saved sample contains one prompt per function. The suite is designed after observing the original ceiling and inspecting some answers during diagnosis. Separate test authors are instructed not to inspect saved answers while constructing their suites. This is not a preregistered or blinded confirmatory study.

Completed: **30/30 saved answers pass, 4,770/4,770 audit checks.** Read the [findings and readiness recommendation](findings.md) and [verification evidence](verification.md).

## Scope and acceptance

Audit all five saved responses for each of the six development functions. Apply the same valid cases to every response for a function. Test only inputs allowed by the original contract. More demanding inputs must remain within the original bounds; changing those bounds would test a different requirement.

Each family receives directed semantic cases, deterministic generated cases, and boundary coverage. Independently authored oracles determine expected values, with hand-checked examples or small exhaustive checks. Cross-check the frozen references as a diagnostic, rather than treating them as the only source of truth. Record the suite, seed, code, cases, and original answer hashes before evaluating candidates.

Execute saved code only through the existing restricted Docker grader and pinned image. Use small batches to avoid its output limit. Separate functional mismatches from execution errors and infrastructure errors. Reproduce any failing batch on individual cases before claiming a concrete functional defect. Retain every outcome and any counterexample; do not repair saved answers or remove difficult cases after inspecting outcomes.

The audit is complete when all 30 responses have recorded outcomes, expected values and input validity have been checked, original artifacts remain unchanged, and the report states both results and limits. Any unresolved scoring or infrastructure issue makes the affected result inconclusive.

## Decision to make after the audit

If valid new cases reveal errors, quantify how many saved implementations fail and identify the missed contract interactions. That would support a claim about weaknesses in the original test coverage, not a claim about prompt sensitivity. New generations would still need a separately frozen prompt comparison.

If all answers pass again, stop expanding this pool merely to obtain failures. Use the audit as evidence that the tested implementations handle a broader valid input sample. A new exploratory prompt comparison should use independently authored tasks and stronger tests from the outset, with a fixed sample, one controlled equivalent-format intervention, better reference isolation, and unchanged requested model and reasoning settings. A further ceiling remains possible and must be reported.

The planned 12-task × 3-format × 2-response experiment is a proposal, not collected data or a power claim. The original conditional pilot 3 remains unlaunched regardless of audit outcomes.

## Reproduce the audit

Use Python 3.12 or newer and a running Docker engine. From the repository root:

```sh
docker pull python@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2
python3.12 -m unittest discover -s audits/composite-robustness -p 'test_*.py' -v
python3.12 audits/composite-robustness/run.py verify
python3.12 audits/composite-robustness/run.py preflight --output work/audit-reproduction/reference
python3.12 audits/composite-robustness/run.py grade --preflight work/audit-reproduction/reference --output work/audit-reproduction/answers --review-note 'Reproduce the committed reviewed suite'
```

Use new output directories for each run. Existing directories are never overwritten. Do not run `freeze` against the committed suite; that command builds the initial snapshot and deliberately refuses to replace it. The verification command checks source, case, saved-answer, and protected original-file hashes. The unit tests regenerate the cases and check the oracles; the committed cases are the inputs to reproduction.

`batches.jsonl` records case IDs, status, observed pass count, detail, and elapsed time for each sandbox invocation. `summary.json` validates complete case coverage for all five responses per function. Its counts must match the batch log. A failed batch produces separate individual-case reproduction files. The unchanged grader does not expose actual return values through its public function, so diagnostic files do not invent them.

The original grader settings are retained, including the four-second wall limit per invocation. Audit invocations contain at most eight cases and keep expected typed output below 48,000 bytes. This batching differs from the original one-batch-per-response calibration, so elapsed times and timeout outcomes are not directly comparable. Input relabelings and related cases are dependent; case-check totals are coverage counts, not independent statistical trials.
