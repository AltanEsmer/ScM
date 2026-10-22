# Composite calibration verification

The starting repository commit was `a562a4f09d9412b92805b9a725016a657af8c59a`. Earlier studies, their runners, inputs and records remain unchanged. The conditional design in `pilots/pilot3/design.md` is retained as the historical rationale; round 2 implements its development gate.

## Preparation before collection

All 18 functions were completed before any development response. Six are development functions and twelve are paired held-out functions with different requested behaviors. The 361 frozen cases include 119 development cases and 242 held-out cases. Five generations per development task imply 595 planned case checks during calibration.

Independent reviewer sessions checked the contracts and oracles. The mathematical lane inspected bounded flow enumeration, resource-indexed grammar derivations, accepted walks and adversarial choices. Additional probes checked 300 version trees, 400 grammar inputs across three behaviors, and 350 walk/game inputs. The semantic lane inspected closures, snapshot restoration, branch isolation, vehicle route enumeration and finite-state edits. These are additional AI-assisted checks, not independent human validation.

Review exposed two missing held-out regression cases: dynamic rather than lexical closure scope could pass every equivalence case, and omitting the counting modulus could pass every optimal-script count case. Both were fixed before freezing. A shadowed closure must return the captured value. An independently checked cost-spectrum count gives minimum cost 60 and 2,026,521,318,286 optimal scripts, whose required residue is 521,304,104. Per-task mutant tests now reject both errors.

Workflow review added enforcement of scheduled dispatch order, the maximum of three concurrent trials, immutable validation-test files, and source-hash binding between calibration and conditional selection. No actionable collection or selection issue remained at freeze. The common code-only output instruction is identical to round 1.

All 18 reference implementations passed the unchanged, pinned Docker grader on their complete case batches. Measured elapsed times were 0.217–0.317 seconds, including container startup, against a four-second limit. Complete typed observations were 7,720–24,017 bytes, below the 49,152-byte preparation target and 65,536-byte hard output limit. See [the measurement table](results/reference-preflight.json). Timing is host-specific and is not a model-generation performance metric.

The new suite has 29 tests covering independent goldens, domain membership, mutation checks, observation size, prompt-clause recovery, balanced schedule, raw answer preservation, no overwrite, unique sessions, dispatch chronology, incomplete infrastructure outcomes, frozen source changes, and the qualification/subset rules. The previous 60 tests also pass. Python compilation and whitespace checks pass. No dedicated type-checker result is claimed.

## Evidence limits

The manifest freezes all development and held-out materials before generation. A separate pilot manifest is required only if the frozen gate succeeds. First final messages are copied unchanged; response hashes and coordinator-observed timestamps support auditability without supplying provider-authenticated transcripts. Requested model/effort are recorded as requested, with unavailable backend model revision and tool traces explicitly represented.

Shared filesystem and tool access remain available to native candidate sessions. Reference inaccessibility, no tool use, session independence, and absence of backend drift cannot be established. The finite-case grader is intended for ordinary generated code and is not hardened against deliberate interpreter tampering. These limits apply to every resulting claim.

## Completed collection and grading

Test contracts were committed in `a8c1e5f`, implementation in `b928b1f`, and the precollection freeze in `7141a528af11c0933810911d79994bbd9c070eaf`. The freeze timestamp is 2026-10-22 18:40:37 UTC. The frozen materials were pushed to the verified public remote during collection.

All 30 first responses were collected from unique fresh native sessions at the requested model and effort, in schedule order, with a maximum of two candidate sessions concurrently. There were no retries, follow-ups, repairs, interim grading or missing responses. Raw records were committed in `79fda31` before the first grading run.

That run evaluated all 30 responses successfully: 30 all-case passes, 595/595 case checks, no functional failures, execution errors, exclusions or infrastructure failures. Every family scored 5/5. Selection records zero eligible families and `not_run_insufficient_eligible_families`. No qualifying-failure review was necessary, and no pilot-3 candidate generation occurred. Frozen inputs still match the manifest.

## Final acceptance

A fresh `git clone --no-local` of `523f99c` passed all 89 tests: 12 root tests, 16 pilot-2 tests, 27 round-1 tests, five uncertainty-helper tests, and 29 new composite tests. All four collected studies passed complete verification: 45, 45, 18 and 30 responses respectively. Regrading round 2 and recomputing selection in that clone produced identical tracked files, including the CSV, report and no-launch decision. The host already had the pinned Docker image. [The final verification log](results/final-verification.txt) records commands and exit codes.

Final Standards review found one documentation issue: the standalone reproduction block omitted the required image pull because the grader uses `--pull=never`. The explicit digest-pinned pull command was added. No material code or evidence findings remained. Final Spec review found no missing requirements or incorrect claims. Both reviews used separate AI sessions and do not constitute independent human validation.

All earlier frozen experiment files and the historical pilot-3 design/draft are unchanged from `a562a4f`. New frozen inputs remain unchanged from `7141a52`. The verified publication remote is `https://github.com/AltanEsmer/ScM.git`; no course files, scratch capture files, credentials or unrelated local material are included.
