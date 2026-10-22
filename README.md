# Prompt sensitivity pilots

Two Scientific Methods pilots investigate whether equivalent prompt variations change the correctness of generated Python functions. Each pilot has three tasks, three variants, and five repetitions per variant, for 45 fresh-session responses.

**Pilot 1:** introductory phrasing changes on three simple tasks; all 45 responses passed. Read [pilot 1 findings](docs/findings.md).

**Pilot 2:** harder tasks with interacting rules and full-specification paraphrases; all 45 responses passed 1,620 case checks. Read [pilot 2 findings](pilots/pilot2/findings.md) and its [reproduction instructions](pilots/pilot2/README.md). Pilot 1 data and frozen inputs are preserved.

**Calibration round 1:** six more complex tasks, one baseline prompt each, three responses per task. All 18 passed; no task met the frozen mixed-outcome selection rule. Read [round 1 findings](calibration/round1/findings.md).

**Composite calibration round 2:** six new development functions, five responses each. All 30 passed all 595 case checks. The twelve distinct held-out functions were frozen before collection, but zero families qualified. Read [round 2 findings](calibration/round2/findings.md) and [reproduction instructions](calibration/round2/README.md).

**Post-hoc robustness audit:** the same 30 composite answers passed 4,770/4,770 checks on 954 unique inputs, including 952 absent from the original tests. No new model responses were collected. Read the [audit findings and next-experiment recommendation](audits/composite-robustness/findings.md) and [reproduction instructions](audits/composite-robustness/README.md). Original results remain unchanged.

**Pilot 3:** [not run](pilots/pilot3/README.md), because the frozen gate required at least three qualifying families. See [how strong the findings are for the report](docs/evidence-strength.md), including suggested report wording.

**Independent format study:** preparation for 12 externally authored competition tasks, three equivalent formats, and two repetitions per format (72 planned responses). The study preserves 2,339 source cases and uses a separately indexed, statement-validated subset of 2,178. Read the [preparation status](studies/format-study1/README.md) and [frozen protocol](studies/format-study1/PROTOCOL.md). No study responses have been collected.

The requested model is `gpt-6.1-sol` with medium reasoning. The earlier pilots were collected through native Codex subagents; the new independent format study uses a separately isolated collection workflow. [Methodology](docs/methodology.md) explains the context controls and unavailable backend evidence.

## Reproduce pilot 1

You need Python 3.12 or newer and a running Docker engine. No Python packages are required for the CLI.

```sh
git clone https://github.com/AltanEsmer/ScM.git
cd ScM
docker pull python@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2
python3 scm.py verify --require-complete
python3 scm.py grade
python3 scm.py report
```

Read the generated report in `results/`. The repository keeps raw responses in `records/`, prompt files in `prompts/`, and the frozen design in `experiment/`.

## Check the tooling

```sh
python3 -m unittest discover -s tests -v
python3 scm.py self-test
```

Generated answers execute inside restricted Docker containers. They are never imported into the host Python process. Expected answers stay outside the candidate container. The grader checks functional behavior against finite cases; passing them does not prove universal correctness.

## Collect a new experiment

Read [the protocol](docs/methodology.md) before collection. The CLI does not launch native Codex subagents. A coordinator starts each fresh session with the exact prompt and requested settings, then saves the first final answer and evidence. The current records must not be overwritten or reused as a new sample.

Create a separately named experiment or repository branch for changes to tasks, prompts, model settings, or grading policy. Freeze the inputs before collection. Do not tune this pilot after inspecting its outcomes.

## Course scope

This repository contains the pilot and its evidence. The literature review, citation screenshots, IEEE LaTeX paper, and presentation remain separate work. See [AI assistance disclosure](docs/ai-disclosure.md) and [acceptance contract](docs/spec.md).

Existing local lecture files are excluded from Git. They are not needed to reproduce this pilot.
