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

Only one requested model and reasoning setting were studied. Provider model revision, temperature, and sampling seed are unavailable. In the earlier native-session pilots and calibrations, new sessions did not inherit the parent conversation, but retained system instructions, tools and shared filesystem access; full tool traces were unavailable. The isolated format study has separate controls described below. The saved artifacts attest to coordinator observations rather than an independently authenticated provider transcript. Code, cases, references and reviews were AI-assisted within one model family, so review errors can be correlated. Independent small-case oracles and constructed optima reduce, but do not eliminate, scoring error.

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

## Post-hoc robustness audit

The 30 saved composite responses were evaluated against 954 unique within-contract inputs, including 952 not present in their original case sets. All 30 passed: 4,770/4,770 checks, with no execution or infrastructure errors. Separately authored oracles, alternative algorithm checks, and a successful frozen-reference preflight support the new expected values. All original study artifacts and the pilot-3 no-launch decision remain unchanged. See the [audit findings](../audits/composite-robustness/findings.md).

This strengthens the narrow statement that these saved implementations handled a broader tested input sample. It reduces concern that the ceiling depended solely on the original sparse tests. It adds no new model responses and no prompt contrast, so the evidence for general prompt robustness remains weak and a positive prompt-sensitivity claim remains unsupported. The audit is post-hoc, uses related and generated inputs, and retains the original generation's shared-filesystem and backend-observability limitations.

That direct comparison was prepared and run as [format-study1](../studies/format-study1/results/findings.md). The earlier recommendation is retained here as the decision that led to the new study; its completed result is recorded below.

## Independent format-study update

The new study collected all 72 frozen responses with the requested `gpt-6.1-sol` and medium reasoning. The backend reported the same alias. All 72 responses passed every retained case, producing 13,068/13,068 successful checks and no missing or infrastructure outcomes. Every task and format cell scored 2/2. The prespecified mean B−A and C−A differences were both zero.

This improves confidence that the **observed** ceiling is not only a property of the earlier AI-assisted custom tasks or shared reference access. The new problems were externally authored, the prompt contents were equivalent across formats, and isolated generation could not read local tests or references. It does not make the absence of a format effect a strong general finding. The 12 selected tasks are public, the retained suites are mostly small relative to full constraints, and the model passed every observed response. The endpoint therefore still cannot distinguish formats on tasks where correctness is uncertain. Provider-reported model identity is not independent attestation of its weights or revision.

Report-ready wording: “In a separately frozen, isolated comparison on 12 selected public programming tasks, 72/72 responses passed their retained test suites across prose, numbered-list, and XML presentations. We observed zero within-task differences in this finite sample. Because every task and format reached the all-case-pass ceiling, the study did not establish that the formats are equivalent or that correctness is generally insensitive to presentation.”

The project now supports a strong methods and reproducibility account, plus precise descriptive negative results. Evidence for a general prompt-sensitivity or prompt-insensitivity claim remains weak. The [preliminary paper plan](preliminary-paper-plan.md) identifies the course requirements and the next writing steps.
