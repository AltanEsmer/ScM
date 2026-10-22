# Verification evidence

The frozen collection is complete. The commands below reproduce the integrity check, tooling checks, and derived results.

## Test-first evidence

The host-score regression initially accepted a forged `{"status":"pass"}` response. `test_stdout_cannot_claim_pass` failed with `pass != invalid_output` before the implementation changed. The focused test log is retained locally at `work/poteto/pilot/host-red.log`.

Bootstrap commit `de1a7d6` defines the acceptance contract. Commit `05ede9f` records the initial behavioral tests. Tests are intentionally incomplete at that commit because implementation follows in a separate commit.

## Preflight review

An independent reviewer found three weaknesses before any programming trial was collected. Candidate stdout could imitate the observation format. Custom classes could imitate built-in type names. Python exit codes could be confused with Docker startup failures. The implementation adds focused regressions, and the methodology explicitly limits the grader to ordinary generated code. It does not claim adversarial interpreter security.

The comment review found no prohibited comments and required no deletions.

## Measured acceptance

- `python3 scm.py verify --require-complete` returned 45 collected and zero missing records.
- `python3 scm.py grade` evaluated all 45 responses using the frozen source and image digest. All passed, with 330 successful case assertions.
- `python3 scm.py report` regenerated the per-task and per-variant table.
- `python3 -m py_compile scm.py grading.py scripts/capture.py` passed. No static type checker was installed, so this is syntax validation rather than a type-check claim.
- `git diff --check` passed.

The local host ran Python 3.14.7 and Docker server 29.8.2. Candidate code ran in the pinned Python 3.12 image. See `results/environment.json` for the image digest and experiment commits.

The protocol and code were frozen in `1ae1851` before the first programming trial. Raw records were committed in `a8af017`. No provider-side token usage, model revision, or full event transcript is available. The records state these limits explicitly.

## Analysis revision after collection

Final review found a reporting defect when Docker fails during a later grading run. The correction changes failure persistence and report counts, not candidate responses, prompts, task cases, or the Docker evaluation logic.

`collection-manifest.json` preserves the original precollection hashes from `1ae1851`. `results/initial-grading.csv` preserves the first full grading run. The current `manifest.json` binds corrected analysis code at `30fd1ba`. The post-fix regrade matched every original trial identifier, session, outcome, case count, and response hash. All 45 responses passed all 330 case assertions again.

## Final checks

The full suite passed 12 tests in 10.115 seconds after the reporting fix. The run covers host scoring, malformed outputs, exact nested types, frozen-input and record integrity, meaningful faulty functions, Docker isolation, time and output limits, container cleanup, unavailable images, and stale-report replacement. The log is [tooling-tests.txt](../results/tooling-tests.txt).

Both independent reviewers reran the infrastructure regression and confirmed the P2 resolved at `30fd1ba`, with no new actionable findings. The final integrity check reports 45 collected records and zero missing. The comment review required no deletions.

The publication check found no tracked lecture PDFs, topic text, environment files, or local work logs. The Git remote was verified as `https://github.com/AltanEsmer/ScM.git` before commits and publication. The existing local course files remain present.

The original manifest matches `collection-manifest.json` exactly. Prompts, task cases, raw responses, the capture helper, and `grading.py` remain unchanged since collection. Only analysis failure handling and reporting changed after the initial grading run.
