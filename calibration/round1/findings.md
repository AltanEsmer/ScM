# Calibration round 1 findings

All 18 first responses passed all frozen cases: 582 successful case checks over six task contracts. Each baseline cell scored 3/3. There were no missing responses, interruptions, infrastructure failures, syntax/runtime failures or timeouts. The frozen selection rule therefore classifies all six tasks as observed ceilings and selects no family for the third pilot.

| Task | All-case passes | Successful case checks | Frozen classification |
| --- | ---: | ---: | --- |
| Unrestricted Damerau–Levenshtein distance | 3/3 | 102/102 | ceiling |
| Minimum-cost bounded circulation | 3/3 | 105/105 | ceiling |
| Directed minimum rooted arborescence | 3/3 | 108/108 | ceiling |
| Minimum-cost finite grammar parse | 3/3 | 84/84 | ceiling |
| Resource-bounded walk with required vertices | 3/3 | 84/84 | ceiling |
| Lexical interpreter with closures and recursion | 3/3 | 99/99 | ceiling |
| Total | 18/18 | 582/582 | zero eligible families |

## What was calibrated

Each task used one clear baseline prompt, repeated in three fresh sessions requesting `gpt-6.1-sol` and medium reasoning. The randomized schedule, prompts, references, 194 case inputs, grader and selection rule were frozen at `09521fa`. Raw responses were committed at `2949e76` before grading. The unchanged Docker grader evaluates functional results, exact built-in types, input preservation and the same execution limits as the earlier pilots.

These tasks require more advanced algorithms or interacting semantics than the previous pool. The graph tasks have larger bounds, signed costs, lower bounds or directed cycles. Grammar parsing includes epsilon rules and zero-cost recursive cycles. The interpreter includes lexical capture, recursive functions and shadowing. This was an intentional increase in complexity, not independently established model difficulty.

## What we learned

This pool did not expose correctness headroom under the current measurement: every observed generation passed. Increasing recognizable algorithmic complexity and adding semantic edge cases was insufficient to produce mixed outcomes in this small sample. That is a calibration result, not a failed experiment to conceal or repair.

There are no observed candidate failures to diagnose. We cannot attribute the ceiling to any particular internal strategy or prove that the complete valid input domains would pass. The three longer random edit-distance pairs also use the reference implementation for their expected values, so agreement on those cases is not independently certified. Other tests combine worked literals, independent exhaustive small-case oracles and constructed optima, as described in [verification](verification.md).

Three repetitions per task are a noisy screen. The label “ceiling” describes the observed 3/3 cell; it does not establish a true success rate of 100%. For illustration only, the exact 95% binomial interval for 3/3 is about 29.2%–100% under independent, identical Bernoulli sampling. Selection and session/task dependence are not accounted for by that illustration. See [the evidence-strength assessment](../../docs/evidence-strength.md).

## Consequence for pilot 3

No family satisfies the frozen one-or-two-passes selection criterion. Selecting one anyway would change the decision rule after seeing the outcomes. Pilot 3 is therefore designed but conditional: a separately frozen development calibration must identify tasks with observed mixed outcomes before its correctness comparison is launched. The [third-pilot design](../../pilots/pilot3/design.md) proposes newly authored compositional contracts, distinct held-out function tasks, and a more controlled format intervention. Those task blueprints are hypotheses to test, not tasks proven difficult by this calibration.

The next development stage should examine realistic combinations of rules and state, rather than assume that a named advanced algorithm or larger input bounds ensure difficulty. It must preserve unambiguous specifications, independently checked goldens, safe runtime margins and complete reporting. Simply hiding or weakening the specification would change what the research measures.

## What this does not establish

Calibration uses one prompt per task, so it cannot estimate a prompt-variation effect. Its 18 responses should not be pooled with the two 45-response prompt pilots into one prompt-sensitivity or model-accuracy statistic. The 582 case checks are dependent within responses and share inputs across repetitions.

Requested model settings are not provider-confirmed backend metadata. Full candidate tool traces, serving revision and sampling controls are unavailable. Fresh sessions retain system context and shared filesystem/tool access. Results remain conditional on those collection limits and the finite test suite.

The saved [per-trial CSV](results/trials.csv), [generated report](results/report.md), [raw answers](records/), [dispatch records](dispatch/) and [frozen manifest](manifest.json) support audit and regrading. No prompt, case, reference or grading change was made after collection began.
