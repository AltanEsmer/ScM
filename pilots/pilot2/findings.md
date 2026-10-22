# Pilot 2 findings

All 45 first responses passed every frozen test, for 1,620 successful case checks. Each of the nine task/variant cells scored 5/5. The observed difference between variants within each task was zero percentage points. No response was missing, interrupted, excluded for infrastructure failure, or left unevaluated.

| Task | A: prose | B: numbered rules | C: formal contract | Successful case checks |
| --- | ---: | ---: | ---: | ---: |
| Weighted job selection | 5/5 | 5/5 | 5/5 | 540/540 |
| Escaped path wildcard matching | 5/5 | 5/5 | 5/5 | 540/540 |
| Scheduled flight itinerary | 5/5 | 5/5 | 5/5 | 540/540 |
| Total | 15/15 | 15/15 | 15/15 | 1,620/1,620 |

## What changed

Pilot 1 changed introductory phrasing on three simple tasks. Pilot 2 used tasks with more interacting constraints: weighted interval selection with three ranking criteria, path wildcard rules with escaping and separators, and flight routing with waiting and route tie-breaking. It rewrote the complete specification in three forms while preserving requirements, bounds, and interfaces. Each task had 36 predefined cases, including semantic mutants rejected before collection.

The requested settings stayed `gpt-6.1-sol`, medium reasoning, and fresh no-history sessions. Both pilots used three variants and five repetitions per task/variant. Pilot 2 used a new randomized dispatch order and the unchanged Docker grader. Full contracts and the clause-equivalence matrix are linked from [the protocol overview](README.md).

## Interpretation

This second pilot again reached the ceiling of the chosen correctness metric. The more complex tasks and stronger prompt variations did not produce an observed functional difference on these cases. There is no failed response to diagnose in this collection.

The result supports the narrower statement that all sampled first responses satisfied the frozen finite tests. It does not show that the prompts always produce equivalent behavior, that all valid inputs would pass, or that larger prompt changes cannot matter. Five repetitions per cell and three selected tasks offer limited sensitivity. The case checks share responses and inputs: 1,620 checks are not 1,620 independent model trials. There were 45 generation trials, and the three tasks are a convenience sample.

Task bounds deliberately allow exhaustive solutions. More interacting rules therefore did not necessarily make these tasks challenging for this model. Difficulty was a design intention rather than an independently measured property. The intervention also combines wording, order, and layout. Comparing pilot 1 and pilot 2 cannot isolate task difficulty from prompt variation because both changed together.

## Collection limits

The model and reasoning values are requested settings, not provider-confirmed model metadata. Temperature, backend random seed, serving model revision, and full tool-event traces are unavailable. No-history sessions retain system instructions and shared tool/filesystem access, so the records cannot prove that every candidate avoided tools or repository files. The coordinator copied each returned first final message without repair and saved hashes and observation timestamps. These records support integrity checking of the saved artifacts, not an independently authenticated provider transcript.

The primary outcome was predefined functional pass rate, not textual identity, runtime efficiency, token cost, or output style. No statistical significance or prompt-equivalence test is claimed. Pilot 1 remains preserved as its own experiment; pooling the 90 responses would conceal the different tasks and interventions.

## Recommended next step

Build a separate calibration pool with more demanding algorithmic and interacting-constraint tasks, still using the same model and reasoning setting. Use a single baseline prompt to identify task families with non-ceiling accuracy. Exclude those calibration instances from the final study, then freeze a held-out task set, equivalent prompt variants, scoring rules, and a larger repetition plan before collection. Keep task selection independent of which prompt variant performs best.

The immediate research lesson is to calibrate task difficulty before expanding repetitions: more runs on tasks that all pass will provide little information about correctness sensitivity. A later study could separately predefine style or efficiency outcomes, but this pilot provides no such outcome claim.

## Evidence

See [per-trial results](results/trials.csv), [generated report](results/report.md), [raw responses](records/), [dispatch evidence](dispatch/), [frozen hashes](manifest.json), and [verification notes](verification.md). Inputs were frozen at `32b1be1`; all raw responses were committed at `ed5f229` before grading. There were no model-response retries, repairs, or post-outcome changes to frozen inputs.
