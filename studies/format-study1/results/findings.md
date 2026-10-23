# Results of the independent prompt-format study

The live backend check passed on 23 October 2026. The isolated client requested `gpt-6.1-sol` with `medium` reasoning, and the backend reported the same model alias. The check returned the exact synthetic marker. It did not use a study task. The backend's reported alias is not independent attestation of its weights or revision.

All 72 scheduled responses were collected in frozen order, once each, in distinct threads. Every saved response used the frozen prompt hash and isolation image. No generation failed or needed a retry. The collection audit verified the unchanged 196-artifact freeze before grading. The generation records are in [`../runs/`](../runs/), and the raw grading records are in [`trials/`](trials/).

## Primary outcome

The frozen grader ran each raw answer against every retained case for its task. All 72 responses passed their complete retained suites. This produced 13,068 successful case checks out of 13,068, with no execution or infrastructure errors. Those case checks are repeated measurements of 72 programs, not 13,068 independent model responses. The saved [analysis](analysis.json) has no unavailable trials.

| Task | Retained cases per response | A prose | B list | C XML |
| --- | ---: | ---: | ---: | ---: |
| 0074 | 143 | 2/2 | 2/2 | 2/2 |
| 0152 | 18 | 2/2 | 2/2 | 2/2 |
| 0250 | 254 | 2/2 | 2/2 | 2/2 |
| 0320 | 237 | 2/2 | 2/2 | 2/2 |
| 0339 | 225 | 2/2 | 2/2 | 2/2 |
| 0402 | 179 | 2/2 | 2/2 | 2/2 |
| 0466 | 135 | 2/2 | 2/2 | 2/2 |
| 0472 | 160 | 2/2 | 2/2 | 2/2 |
| 0581 | 205 | 2/2 | 2/2 | 2/2 |
| 0760 | 334 | 2/2 | 2/2 | 2/2 |
| 0799 | 50 | 2/2 | 2/2 | 2/2 |
| 0979 | 238 | 2/2 | 2/2 | 2/2 |

Each task's B minus A and C minus A success differences were zero. The prespecified equal-task mean contrasts were also zero. The observed difference is exactly zero in this selected sample under this finite test suite. The result does not establish equivalence of the formats or a small effect in a broader task population.

## Interpretation and limits

This study improves task authorship and reference isolation over the earlier custom-task pilots. The 12 tasks came from an external public dataset, prompt contents were recoverably equivalent, allocation was balanced and frozen, and the generation containers could not browse local references, tests, or earlier answers. The positive result for the method is that the complete protocol ran and produced auditable paired data without missing observations.

The primary correctness outcome still reached a ceiling. With no failures, this sample cannot reveal whether one format changes the chance of failure on tasks that are difficult for the model. It supports only the statement that no correctness difference was detected here. Public tasks may have been present in training, and many retained tests use small inputs relative to statement limits. The study does not establish full-constraint correctness, runtime quality, training independence, provider revision, or behavior on other models. Two repetitions per task and format give limited information about response variability. No significance or equivalence test was prespecified, and none is claimed.

For the course report, state the result as a measured ceiling and make the measurement problem part of the discussion. A future test of prompt sensitivity should define a fresh task source and a prespecified failure-exposing outcome, then freeze its tasks, tests, prompts, and analysis before collection. Do not select a new outcome from the 72 saved answers and present it as confirmatory evidence.

## Reproduce the summary

From the repository root, run:

```sh
python3 studies/format-study1/prepare.py verify
python3 studies/format-study1/analyze.py studies/format-study1/results/outcomes.json
```

The generation and grading records are saved. Replaying them would create new provider responses or rerun untrusted code, so the commands above verify the frozen materials and recompute the descriptive summary from the saved outcomes.
