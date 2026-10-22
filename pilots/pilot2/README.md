# Pilot 2: harder tasks and full-contract paraphrases

This follow-up keeps the requested `gpt-6.1-sol` model, medium reasoning, fresh no-history sessions, three variants, and five repetitions from pilot 1. It changes the tasks and rewrites whole specifications instead of introductory sentences. Both changes occur together; comparing the pilots cannot isolate either effect.

The tasks are weighted interval selection with three ranking criteria, escaped path wildcard matching, and scheduled flight routing with three ranking criteria. Bounds permit exhaustive solutions. Harder means more interacting requirements and targeted regression cases; this is a design intention, not an independently calibrated difficulty score.

A is connected prose, B is a numbered specification, and C is a formal contract. They preserve the information, input bounds, output type, and behavior. Wording, order, and layout change jointly. See [clause equivalence](equivalence.md), [frozen protocol](protocol.json), and [randomized schedule](trials.json).

## Reproduce

From the repository root, with Python 3.12+ and Docker running:

```sh
python3 pilots/pilot2/run.py self-test
python3 pilots/pilot2/run.py verify --require-complete
python3 pilots/pilot2/run.py grade
python3 pilots/pilot2/run.py report
```

The pinned Docker image is the same as pilot 1. The independent driver imports unchanged root `grading.py`. Raw first-final responses and requested-session metadata live in `records/`; coordinator dispatch observations and attached session paths live in `dispatch/`. Both are tracked so verification works after cloning. `manifest.json` hashes the inputs and grader before any dispatch. `results/trials.csv` and `results/report.md` are derived artifacts.

## Collection and limits

A coordinator dispatches the exact prompt in the frozen randomized order, at most three trials concurrently. Each research session is newly spawned with no inherited conversation, the requested model, and medium reasoning. No repairs, follow-up hints, retries, or outcome-based case changes are allowed. The coordinator records the first returned final message verbatim, including any formatting. Capture timestamps are coordinator observations, not backend generation timestamps.

No API key is required. Native Codex subagents retain system instructions, tools, and access to a shared filesystem. No-history does not establish sandbox isolation. Full tool traces, actual serving model revision, temperature, and seed are unavailable. Evaluation isolates ordinary candidate execution in Docker but is not designed to resist interpreter-level malicious candidates.

The primary outcome is all-cases functional pass rate among evaluated responses in each task/variant cell. Candidate exceptions and formatting failures count as failures; infrastructure failures, missing responses, and responses not evaluated are reported separately. Five repeats per cell support descriptive findings only. The finite case set and any ceiling effect limit sensitivity. No significance or equivalence claim is planned.

The study design, code, test fixtures, reference implementations, raw candidate answers, grading, and documentation were produced with AI assistance under user direction. Independent review here means another agent session, not a human or an independent model family.
