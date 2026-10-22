# Preparation verification

Baseline: `d4586c02c30380545376f69b3bc74776e4e9c655`. Remote: `https://github.com/AltanEsmer/ScM.git`. Source and curation were committed in `ba60911`; protocol, equivalent prompts, allocation, grader, analysis, and isolated collection tooling in `8c015c6`. Infrastructure-only recovery tooling and its tests were committed in `89dc91d`. Final freeze publication is recorded in Git history.

This is preparation evidence, not a model-result report. There are zero study generations, zero calibration generations, and zero live provider canaries in this workstream. No real provider credentials were read. The literal offline fixture answer is synthetic data.

## Source validation

The final pool has twelve external tasks, six MEDIUM and six HARD according to the pinned dataset, with 2,339 original test cases and 2,178 curated cases. All 161 omissions have preserved source indices, hashes, and statement-domain or expected-output-shape reasons. Original and retained input/output strings are unchanged. The task loader recomputes validators and requires every and only accepted source case, preventing arbitrary removal of a failing reference case.

The source data required pre-freeze amendments. Preserve initial selections, domain-invalid cases, semantic defect evidence, excluded whole tasks, and superseded reference reports. Task 0778 was replaced only after independent derivation proved a wrong expected answer on a valid input; the next task in the same deterministic ranking, 0799, was used. Case 25 of 0799 has a generic parser reason `Input truncated`, but the [provenance correction](source/case-0799-25-provenance-correction.json) explains that the expected-output token sequence is truncated. There is no answer repair or target-model outcome selection.

This is a curated subset study, not an official TACO benchmark score. The external suites mostly have small inputs and cannot validate full-bound runtime complexity. See the limitations and examples in the protocol.

## Tests and runtime evidence

The [new-tooling log](verification-checks.txt) records 26 passing Python tests, including three actual Docker integration tests, and seven mocked HTTPS/auth checks. Commands:

```sh
FORMAT_STUDY_DOCKER_TESTS=1 python3 -m unittest discover -s studies/format-study1/tests -v
python3 -m unittest discover -s studies/format-study1/source -p test_validators.py -v
python3 -m unittest discover -s studies/format-study1/isolation -p 'test_*.py' -v
node studies/format-study1/isolation/test_live_transport.mjs
```

Tests cover all 36 exact prompt reconstructions, balanced and reproducible 72-trial scheduling, immutable original-to-curated subset identity, invalid fixture rejection, manifest tampering and extra artifacts, observed-success retention in incomplete summaries, infrastructure gating, candidate exit-code spoof rejection, and at-most-once ordered dispatch. Two additional recovery tests verify byte-preserved failed attempts, full-task sequential replay, and refusal to recover semantic failures. The source validator tests include positive and negative cases for every selected task. Without the environment switch, the three Docker integration tests are intentionally skipped.

All 98 previous tests also pass: 12 root, 16 pilot-2, 27 calibration-1, five uncertainty-helper, 29 calibration-2, and nine robustness-audit tests. Each was run once during this preparation with `python3 -m unittest discover` against its original test directory. No previous results were regenerated.

[Grader sandbox proof](grader-sandbox-proof.json) binds the current grader hash and records actual container checks: non-root execution, read-only code/input, absent expected answers, disabled network, output and time limits, candidate exit codes 125/126/127 remaining execution errors, and a genuinely missing Docker image remaining infrastructure failure. The ten-second clock excludes container creation and includes start/attach overhead. Cleanup or attach failures produce unavailable infrastructure records, not candidate semantic failures.

[Offline isolation proof](isolation/offline-evidence.json) exercises Codex CLI 0.157.1 against a non-forwarding synthetic provider. It records requested `gpt-6.1-sol`, medium reasoning, and an empty tool array; no host mounts; UID 65534; read-only root; dropped capabilities; blocked direct public and host-gateway connections; and absent reference/test/old-answer canaries. The immutable generation image is `sha256:f71e1bcef67eb5499429a0c4543e9ccf1d4ee5e4f3d1f47f7cb38738e066b86d`. Runtime module hashes inside the image match reviewed host bytes. The proof, launch gate, and freeze bind those bytes, preventing stale-image reuse from receiving fresh source attestation.

Offline proof does not establish live backend compatibility. A future synthetic live canary must confirm the fixed authenticated route and provider-reported model identity. Unknown or mismatched identity blocks collection. No fallback is permitted. The host and Docker daemon remain trusted, and provider internals and training contamination are outside this boundary.

The first final-pool reference attempt had one infrastructure error: task 0320, evaluation index 159 (source index 160), exceeded the execution clock and then Docker cleanup timed out. The original report, including its prior timeout status, remains in `reference-attempts/attempt-1/`. Docker responded normally afterward and no failed-case container remained. `recover_references.py` permits one sequential replay of the entire affected task only when every failure is an infrastructure error and grader/source/reference/evaluation hashes are unchanged. It refuses semantic or ordinary execution failures. The recovery log and final report retain both attempts; no test was removed or changed. This is reference preflight recovery, not a retry of a model generation. Hardware scheduling can affect wall-clock grading; future candidate grading is sequential.

## Independent review and preservation

Separate Spec and Standards reviewer sessions examined statement constraints, all selected validators, source-subset identity, prompt reconstruction, schedule, analysis, grader lifecycle, isolation, model settings, credentials, redirects, and retry controls. Findings fixed before freeze: incomplete summaries omitted observed successes; candidate stderr could imitate a Docker failure; and reused images lacked runtime-source hash binding. Reviewers verified the corrections. These are independent AI sessions within one model family, not independent human or cross-model validation.

All 643 protected pre-existing file hashes match the baseline snapshot. Only the root README receives navigation/context updates outside the new study directory. Original pilot, calibration, audit, and pilot-3 decision files are unchanged.

Whitespace checks pass for project-authored code and documentation. Verbatim upstream README/license text and source-preserving generated prompts retain original whitespace; those known provenance artifacts are excluded from whitespace cleanup.

## Readiness

The final [reference-validation report](reference-validation.json) is **PASS: twelve tasks, 2,178/2,178 cases** with current grader, original-task, supplied-reference, and curated-case hashes. All 237 cases of the affected task passed its explicit sequential recovery. The original first-attempt log retains the infrastructure failure; the final report links the recovery log and original report by hash.

The freeze is preparation only: 36 equivalent prompts and 72 `NOT_RUN` schedule rows, with zero candidate responses. A live provider canary remains a separate required gate. No study run is authorized by this preparation record.

Manifest status: `FROZEN_NOT_RUN`; all 196 protected study artifacts verify. Manifest SHA-256: `b435538e8c83ff065dbb2ecb8fd4db679ea1d80c70f08c26a12f3c4d0d2c3f4e`. The top-level study README and this verification narrative are outside the hash set so publication metadata can be appended without changing experimental materials.
