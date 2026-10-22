# Pilot 2 verification

## Before collection

The dataset and recording contracts were committed in `1a794b1`; implementation and experimental inputs followed in `02777f8`. An independent agent reviewed semantic equivalence, task cases, schedule, and recording behavior before collection. It found and resolved two issues: itinerary prose needed to explicitly require the goal destination and list output; wildcard coverage needed positive ASCII newline cases and a no-DOTALL mutant regression. The recording driver was also corrected to include dispatch evidence in the public repository before freezing.

All 16 pilot2 tests passed on Python 3.12.13 before collection. They cover independent case generation/reference agreement, mutation regressions, prompt inventory, exact answer preservation, exclusive recording, unique sessions, protocol validation, frozen-input integrity, portable dispatch evidence, interrupted collection, infrastructure failures, and stale results. Each reference passed all 36 cases in the pinned Docker image. The original grader's 12 tests also passed, including isolation, time/output limits, malformed outputs, and infrastructure behavior.

Inputs were frozen in `32b1be1cfc56f14440698b2463bb51d731061da6` before the first dispatch. The manifest binds tasks, references, prompts, protocol, schedule, generator, equivalence document, new driver, and unchanged root grader. The root pilot remains an independent, unchanged experiment.

## Reproduction scope

The checked-in records support regrading and audit of coordinator observations. Requested model settings are recorded, but actual provider model revision and random sampling controls cannot be verified. Raw answers are first final messages copied without repair by a collection coordinator. A fresh child session has no inherited conversation but retains system instructions, tools, and shared filesystem access. Full tool-event traces are unavailable.

Python syntax compilation is not static type checking. No external Python dependencies or dedicated lint configuration are introduced. Whitespace validation uses `git diff --check`. Candidate execution uses the existing pinned Python 3.12 Docker image.

## Completed collection and analysis

All 45 unique sessions completed, with no missing or interrupted trials. Evidence records the requested `gpt-6.1-sol` model, medium reasoning, and no-history dispatch. Sessions are `/root/python_044/p2_001` through `/root/python_044/p2_045`; the parent agent was a collection coordinator, not an additional research sample. The frozen randomized order was preserved. Raw records and dispatch observations were committed as `ed5f229` before grading.

`python3.12 pilots/pilot2/run.py verify --require-complete` returned 45 collected, zero missing, and zero interrupted. The first full Docker grading passed all 45 responses and all 1,620 case checks, with no infrastructure failures or exclusions. `python3.12 scm.py verify --require-complete` still reports all 45 pilot1 records intact. Python syntax compilation passed for the new driver and case builder.

All pilot1 files are byte-for-byte unchanged against `582e8eb` apart from the root README, which now links both studies. Pilot2 frozen inputs are unchanged from `32b1be1`. No grading-policy revision or test-suite change followed collection.

## Final review and portability

Two independent agent reviews found no remaining actionable issues. The semantic reviewer checked the final findings against the CSV, including the ceiling effect, limited repetitions, and dependence between case checks. The standards reviewer confirmed integrity, reporting denominators, and preservation of pilot1. Dispatch observations follow the frozen schedule and show a maximum of two trials in flight, within the allowed three.

A fresh `git clone --no-local` into a temporary directory passed complete verification for both pilot2 and pilot1 without relying on ignored local capture files. The new driver and generator compile under Python 3.12.13. `git diff --check` passes. Reviewers also reran the 16 pilot2 tests successfully; the unchanged grader's 12 tests passed during acceptance. No tracked course PDFs, environment secrets, or local scratch files were added. The verified publication remote is `https://github.com/AltanEsmer/ScM.git`.
