# Harder task-pool calibration

This is a separate exploratory calibration using six programming tasks, one baseline prompt per task, and three fresh responses per prompt. Requested settings remain `gpt-6.1-sol`, medium reasoning, no inherited conversation. It measures observed task difficulty, not prompt sensitivity.

The selection rule is frozen before generation: a task with one or two all-case passes out of three evaluated responses is eligible for priority family selection. Three passes is an observed ceiling; zero is an observed floor requiring diagnosis. Incomplete cells cannot qualify. These are screening labels, not precise estimates of population difficulty. The third pilot is designed after this calibration and is not collected here.

Read the [completed findings](findings.md), [verification evidence](verification.md), and [report-strength assessment](../../docs/evidence-strength.md).

## Reproduction

Use Python 3.12+ and a running Docker engine. From the repository root:

```sh
python3.12 calibration/round1/run.py self-test
python3.12 calibration/round1/run.py verify --require-complete
python3.12 calibration/round1/run.py grade
python3.12 calibration/round1/run.py report
```

The pinned Docker image and `grading.py` are unchanged from the earlier pilots. `tasks.json` contains frozen cases and reference implementations. Its two source modules document independent exhaustive small-case oracles and larger constructed cases. Cases using the reference itself for expected values are explicitly identified; reference agreement alone is not independent validation.

`manifest.json` freezes code, protocol, schedule, prompts, generators, cases, and references before dispatch. `dispatch/` and `records/` retain coordinator observations and the first final answer without repair. `results/trials.csv` and `results/report.md` are derived by the grader. No model retries or outcome-based edits to frozen inputs are allowed.

## Limits

Native subagents do not expose the serving model revision, temperature, or sampling seed. The requested settings are recorded, but cannot be independently confirmed against backend metadata. No-history sessions retain system instructions and shared tool/filesystem access; full tool traces are unavailable. The experiment cannot establish that all candidates avoided repository files. Saved answer hashes verify the copied artifact, not an authenticated provider transcript.

The unchanged grader isolates ordinary generated Python code. It is not secure against deliberate interpreter tampering. A case combines functional output and input-preservation checks. Case checks within a response are dependent; they are not independent model generations. Execution errors abort a batch, and a zero case count then does not describe every preceding case.

Task design, implementation, data generation, review, model collection, analysis and documentation use AI assistance under user direction. Independent reviewers are separate sessions from the same model family, not independent human experts. Both previous pilots remain frozen and unchanged.
