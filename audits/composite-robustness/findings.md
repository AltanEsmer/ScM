# What stronger tests reveal about the composite ceiling

This is a post-hoc audit of the 30 existing composite-calibration responses. It does not add model responses, compare prompt variants, or revise the original 30/30 result and 595/595 checks. The original conditional pilot-3 decision remains unchanged.

## Coverage and validation

The audit contains 954 unique input dictionaries across the six original contracts. Two overlap with original cases; 952 are additional inputs. Each function's five responses receives exactly the same cases. Related cases and relabelings are dependent, so test counts are not independent statistical observations.

| Function | Original cases per answer | Audit cases per answer | Main additions |
| --- | ---: | ---: | --- |
| Versioned circulation | 20 | 142 | Branching version ancestry, infeasible ancestors with feasible descendants, signed costs, self-loops, full arc/version bounds |
| Budgeted grammar parsing | 20 | 169 | Nullable and recursive rules, negative costs, alternative resource allocations, successful length-three/four derivations |
| Store interpreter | 19 | 160 | Lexical capture, aliasing, nested snapshots/restores, handle-ID reuse, lazy branches, node/depth/evaluation limits |
| Pickup and delivery | 22 | 158 | Inclusive windows and deadlines, service durations, duplicate requests, directed independent time/cost matrices, four-request boundaries |
| Automaton routes | 19 | 147 | Signed loops, continued travel after acceptance, product states, resource bounds, vertex relabeling |
| Constrained edits | 19 | 178 | Longer Unicode inputs, multiple modes/states, operation/output limits, mode-dependent cost tradeoffs, insertion after input exhaustion |

Expected results come from separately authored audit oracles. Checks use alternative algorithms and literal examples: balance-state dynamic programming for flow enumeration; leftmost derivation expansion for span parsing; a recursive interpreter for the continuation machine; event permutations for route dynamic programming; exhaustive tiny walks for forward resource relaxation; and exhaustive tiny scripts for edit-state Dijkstra search. Counts and categories are in the [manifest](frozen/manifest.json).

All 954 expected results also agree with the frozen references when executed through the unchanged restricted Docker grader. The [reference preflight](results/reference-001/summary.json) contains 122 passing batches. This agreement reduces scoring-error risk but is not independent human validation. The code, oracles, and reviews use AI assistance within one model family.

The suite was committed as `1614df0` before running any saved answer against it. It was designed after observing the original ceiling and after the lead inspected selected saved solutions in the preceding diagnosis. Generator authors were instructed not to read saved answers. The audit is post-hoc and cannot be described as fully blinded or preregistered.

## Results

**All 30 saved answers passed all audit cases: 4,770/4,770 case checks in 610 batches.** There were no functional mismatches, syntax/runtime errors, timeouts, output-limit errors, infrastructure errors, missing responses, or individual-case reproduction runs.

| Function | Answers passing every audit case | Passing checks |
| --- | ---: | ---: |
| Versioned circulation | 5/5 | 710/710 |
| Budgeted grammar parsing | 5/5 | 845/845 |
| Store interpreter | 5/5 | 800/800 |
| Pickup and delivery | 5/5 | 790/790 |
| Automaton routes | 5/5 | 735/735 |
| Constrained edits | 5/5 | 890/890 |
| Total | 30/30 | 4,770/4,770 |

The [per-answer summary](results/answers-001/summary.json) and [batch log](results/answers-001/batches.jsonl) retain every result. All 625 protected original files and all 30 answer hashes remain unchanged. The tooling checks pass all 98 tests; see [verification evidence](verification.md).

The audit found no counterexample to a saved implementation. It reduces concern that the original ceiling was solely an artifact of the particular small case sets. It does not prove universal correctness, task independence, absence of reference access during the original generation, or prompt insensitivity. The audit adds input coverage, not new independent model responses. It supplies no causal comparison between prompts.

## Why more composite calibration is unlikely to help

The contracts remain bounded problems with straightforward exact methods. A circulation snapshot has at most 729 flow assignments, and four pickup/delivery requests have at most 2,520 complete precedence-respecting event orders before further feasibility pruning. The route automaton has at most 1,000 resource/vertex/state combinations. These limits follow directly from the frozen task bounds.

The edit task charges by operation and mode, independently of source or emitted character. Source content therefore matters only through its length. Larger tests exercise more states without changing that simplification. Composite specifications can combine many clauses while leaving an accessible exact algorithm.

These observations explain why adding clauses did not necessarily make the pool difficult for this configuration. They are a plausible interpretation, not a controlled experiment on the cause of the ceiling. Uncovered errors and shared oracle mistakes remain possible. Some random inputs are infeasible, and structured templates and relabelings provide narrower diversity than independently authored tasks.

## Recommendation for the next prompt experiment

**Stop calibrating this pool. Prepare a new exploratory prompt comparison, but do not launch it until its task source, tests, isolation, and protocol are fixed.** The audit gives no reason to keep enlarging these six tasks merely to obtain failures. The existing conditional pilot 3 remains unlaunched; changing its gate after seeing this audit would change the original study.

Use a new study identifier and the same requested `gpt-6.1-sol`, medium setting. Select a fixed pool of independently authored problems, using external difficulty information rather than this model's observed failures to choose the sample. Freeze comprehensive tests and independently checked expected answers before generation. Selection should not require each task to show mixed baseline outcomes.

Change one prompt feature at a time. A proposed exploratory design is 12 distinct problems × three equivalent formats × two fresh responses, 72 generations. Preserve every requirement and output instruction across prose, list, and XML formats; randomize and balance order. This is a bounded exploratory design, not an adequately powered confirmatory study. Report per-task outcomes and the equal-task differences between formats, with task-aware uncertainty appropriate to the small sample. Do not pool case checks as independent trials or claim equivalence from a null result.

Use a generation channel that enforces isolation from test and reference files. The previous native sessions shared filesystem and tool access; a request not to inspect files does not establish technical isolation. If stronger isolation cannot be achieved, document that limitation before collection and narrow the intended claim. Retain first responses, available model metadata, timestamps, and tool traces where supported.

Readiness is therefore partial: the saved-answer audit is complete, but the replacement experiment's materials and generation controls still need preparation. Do not run another baseline-only calibration on this pool. A new direct comparison can still yield a ceiling or a null effect; neither should trigger silent task replacement or prompt tuning.

## Suggested report wording

> A post-hoc robustness audit evaluated the 30 saved composite-calibration responses against 954 unique within-contract inputs, including 952 absent from the original tests. All responses passed, giving 4,770 successful case checks. Separately authored oracles, alternative small-case checks, and frozen-reference preflight supported the expected results. Original study artifacts and the decision not to launch the conditional third pilot were preserved. The audit broadens the observed correctness coverage but provides no prompt-effect comparison and does not establish universal correctness or prompt insensitivity.
