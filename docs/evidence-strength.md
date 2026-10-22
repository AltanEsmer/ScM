# How strong is the evidence for the research report?

The work supports an exploratory methods report. It does not yet support a general claim that the model is insensitive to prompt wording, or that a particular wording improves accuracy. The strongest contribution is an auditable experiment and a documented process for detecting ceiling effects and calibrating task difficulty.

## What the completed prompt pilots establish

Pilot 1 recorded 45/45 functional passes over three tasks; pilot 2 recorded another 45/45 over three different tasks. Every task/variant cell contained five responses and scored 5/5. The observed within-task correctness differences were zero. These statements are conditional on the frozen finite cases and recorded session settings.

The 90 responses do not represent 90 independently sampled tasks. There are six task contracts across two different interventions. The case checks within each response are also dependent. Pooling everything into a single model-accuracy estimate would hide these differences. The pilots provide narrow evidence of success on the tested contracts, with little information about correctness sensitivity once all scores reach the ceiling.

| Proposed claim | Assessment |
| --- | --- |
| All recorded responses in pilots 1 and 2 passed their frozen cases | Well supported by saved artifacts and repeatable grading, conditional on fixture correctness |
| We observed no correctness difference among the tested variants on these six tasks | Supported as a descriptive result |
| The model is generally prompt-insensitive | Unsupported |
| The variants are statistically equivalent | Unsupported; no equivalence margin or adequately powered equivalence test was specified |
| Calibration failures demonstrate prompt sensitivity | Unsupported: calibration uses one prompt per task |
| Three calibration responses determine a task's true difficulty | Unsupported; they provide a noisy screening signal |

## Why small samples matter

Under an idealized model of independent Bernoulli trials with a fixed success probability, exact two-sided 95% Clopper–Pearson intervals are:

| Observed passes | Illustrative interval |
| --- | --- |
| 0/3 | 0.0%–70.8% |
| 1/3 | 0.8%–90.6% |
| 2/3 | 9.4%–99.2% |
| 3/3 | 29.2%–100.0% |
| 5/5 | 47.8%–100.0% |

These calculations illustrate the imprecision of small cells. They are not selection-adjusted study confidence intervals, proof that sessions are independent, or intervals for differences between prompts. They do not account for task sampling, shared system context, backend dependence, or selecting families after inspecting calibration outcomes. The method inverts binomial tails, following [NIST's exact-binomial definition](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). Reproduce the table with `python3.12 analysis/uncertainty.py`; the saved values are in [uncertainty illustrations](../calibration/round1/results/uncertainty-illustrations.json).

## Threats that remain

Only one requested model and reasoning setting were studied. Provider model revision, temperature, and sampling seed are unavailable. New sessions do not inherit the parent conversation, but retain system instructions, tools and shared filesystem access; full tool traces are unavailable. The saved artifacts attest to coordinator observations rather than an independently authenticated provider transcript. Code, cases, references and reviews were AI-assisted within one model family, so review errors can be correlated. Independent small-case oracles and constructed optima reduce, but do not eliminate, scoring error.

The prompt interventions changed wording and, in pilot 2, ordering and layout together. The tasks are a convenience sample, and the pilots changed both tasks and intervention strength. Their comparison therefore cannot isolate either change. Any future study restricted to families selected by calibration will need to limit its claims to that selected population.

## Relation to prior research

Other work has found substantial sensitivity to meaning-preserving formatting on different models and settings. Our small ceiling results do not replicate or refute those experiments. See [Sclar et al., ICLR 2024](https://arxiv.org/abs/2310.11324). [ProSA, EMNLP Findings 2024](https://aclanthology.org/2024.findings-emnlp.108/) also reports variation in sensitivity across datasets and models. These studies motivate broader measurement; their effect sizes must not be attributed to our model or data.

## How to present the project

Frame the report as an exploratory investigation of measurement sensitivity: initial pilots reached a ceiling, motivating two separately frozen difficulty calibrations and a conditional held-out experiment that did not launch. Report every task and exclusion, retain the negative results, distinguish planned work from collected data, and disclose AI assistance. Use descriptive results as the main evidence. A stronger claim about prompt effects needs replicated differences across more independently designed tasks, a controlled intervention, a prespecified analysis, and uncertainty that respects the task grouping.

## Calibration update and report-ready wording

Calibration round 1 produced 18/18 all-case passes and 582 successful case checks. Composite calibration round 2 then produced 30/30 passes and 595 successful checks across six new development functions, five responses per function. All six cells in each round were observed ceilings; zero families qualified. In round 2, twelve distinct held-out functions and all prompt formats were frozen before development outcomes, and the gate required at least three families with mixed outcomes and a validated functional failure. Pilot 3 therefore did not launch. See [round 2 findings](../calibration/round2/findings.md).

These rounds add evidence that the selected tests did not expose failures in the documented setup. They add no prompt-effect comparison, because each uses a single prompt per task. The report's strongest evidence remains the saved observations and the auditable decision not to launch an unqualified pilot. The repeated ceilings do not establish that errors are absent elsewhere or that stronger prompt changes would have no effect.

Suggested report text:

> Two exploratory prompt-variation pilots produced 45/45 functional passes each, with no observed within-task accuracy differences. Two separately frozen baseline calibrations on six tasks each produced 18/18 and 30/30 passes. The second calibration used composite contracts and froze twelve distinct held-out functions before collecting development responses. No family met the predefined qualification rule, so the conditional third pilot was not run. These ceiling results prevented an informative estimate of correctness sensitivity in the selected pools. The findings are limited by small per-cell samples, finite cases, selected task contracts, one requested model configuration, shared tool and filesystem access, and incomplete backend observability.

For a course or exploratory research report, this is a defensible account of experiment design, negative results and methodological learning. For a broad empirical claim about prompt robustness, the evidence remains weak. A positive prompt-sensitivity claim is not supported by the current data. Statistical equivalence, general accuracy and cross-model conclusions would overstate the evidence.
