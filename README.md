# Prompt sensitivity pilot

A Scientific Methods pilot measures whether three introductory phrasings change the correctness of generated Python functions. The study has three tasks and five repetitions per phrasing, for 45 planned fresh-session responses.

**Result:** all 45 responses passed the frozen tests. Read [pilot findings](docs/findings.md) for interpretation and limits.

The requested model is `gpt-6.1-sol` with medium reasoning. This is a pilot collected through native Codex subagents. [Methodology](docs/methodology.md) explains the context controls and unavailable backend evidence.

## Reproduce the analysis

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
