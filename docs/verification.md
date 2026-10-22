# Verification evidence

This file will record commands, outcomes, independent review, and experiment counts after execution. It is not a declaration of completion.

## Test-first evidence

The host-score regression initially accepted a forged `{"status":"pass"}` response. `test_stdout_cannot_claim_pass` failed with `pass != invalid_output` before the implementation changed. The focused test log is retained locally at `work/poteto/pilot/host-red.log`.

Bootstrap commit `de1a7d6` defines the acceptance contract. Commit `05ede9f` records the initial behavioral tests. Tests are intentionally incomplete at that commit because implementation follows in a separate commit.

## Preflight review

An independent reviewer found three weaknesses before any programming trial was collected. Candidate stdout could imitate the observation format. Custom classes could imitate built-in type names. Python exit codes could be confused with Docker startup failures. The implementation adds focused regressions, and the methodology explicitly limits the grader to ordinary generated code. It does not claim adversarial interpreter security.

The comment review found no prohibited comments and required no deletions.
