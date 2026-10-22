# Composite calibration results

All 30 first responses passed every frozen case: **595/595 case checks**. All six development functions scored 5/5, so every family is an observed ceiling. **Zero families qualified; pilot 3 was not run.** No generation, grading or infrastructure outcome was excluded.

## Observed results

| Family | Development function | All-case passes | Case checks passed | Classification |
| --- | --- | ---: | ---: | --- |
| F1 | `versioned_circulation_costs` | 5/5 | 100/100 | Ceiling |
| F2 | `budget_parse_cost` | 5/5 | 100/100 | Ceiling |
| F3 | `store_program_result` | 5/5 | 95/95 | Ceiling |
| F4 | `pickup_delivery_cost` | 5/5 | 110/110 | Ceiling |
| F5 | `automaton_route_cost` | 5/5 | 95/95 | Ceiling |
| F6 | `constrained_edit_cost` | 5/5 | 95/95 | Ceiling |

The requested configuration was `gpt-6.1-sol`, medium reasoning, fresh native sessions with no inherited conversation. The 30 sessions followed the frozen randomized schedule, with at most two candidates running concurrently. The coordinator saved the first final message unchanged; there were no retries, follow-ups, repairs or interim grading. All 30 were collected before the first grading run.

The six development and twelve held-out tasks, all prompts, cases, references, validation checks, schedule and scoring code were frozen in `7141a528af11c0933810911d79994bbd9c070eaf` before dispatch. The freeze was pushed to the public repository during collection. Raw responses and provenance were committed in `79fda31` before grading. The [CSV](results/trials.csv), [generated report](results/report.md), [manifest](manifest.json), and [selection decision](../../pilots/pilot3/selection.json) retain the evidence and source hashes.

## Gate decision

The frozen rule requires five evaluated responses, one through four all-case passes, and at least one independently validated functional mismatch in each qualifying family. A minimum of three families is required to launch pilot 3. No family has a mismatch or mixed outcome. There is consequently no failure-validation artifact, selected task subset, pilot working protocol, pilot manifest or pilot response collection.

The twelve held-out contracts and 36 format prompts remain pre-frozen materials. Reference acceptance does not mean that model generations on those tasks would pass, fail or show format sensitivity. Their candidate difficulty was not measured. The historical [conditional design](../../pilots/pilot3/design.md) remains available alongside the [current status](../../pilots/pilot3/README.md).

## Interpretation for the report

This round failed to establish the intended range of observed task difficulty. Combining several rules in each contract did not produce any failed generations on the tested inputs under the recorded setup. That is a useful calibration outcome; it is not evidence that the entire input domains are easy or that the model is generally robust to prompt changes.

Only one baseline prompt was used per development task. Therefore this calibration contains no prompt contrast and cannot show either sensitivity or insensitivity to prompt wording or format. The earlier two prompt pilots still supply the project's actual prompt comparisons, both with observed zero differences at ceiling. This round adds a documented unsuccessful attempt to make a conditional third comparison informative.

Five passing responses give a noisy task-level screening observation. Under the idealized iid-binomial illustration already documented in [the evidence assessment](../../docs/evidence-strength.md), 5/5 has a two-sided exact 95% interval of approximately 47.8%–100%. This is not a selection-adjusted study interval or evidence that sessions are independent. The 595 checks are nested within 30 generations and six task contracts, not 595 independent model trials.

The report can credibly describe an exploratory methods study with reproducible artifacts, negative findings, and an enforced stopping rule. It cannot claim a prompt-sensitivity effect, statistical equivalence, or general prompt robustness. Native sessions retain system instructions, tools and shared filesystem access; reference isolation and tool abstention cannot be established. Serving revision and sampling settings are unavailable, while cases, implementations and reviews are AI-assisted. These limitations materially constrain interpretation.

Any further difficulty calibration would be a new study, requiring a separate rationale and freeze. This round does not automatically trigger increasingly difficult tasks until an effect appears.
