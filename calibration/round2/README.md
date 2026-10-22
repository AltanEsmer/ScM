# Composite task calibration

This experiment implements the [conditional third-pilot design](../../pilots/pilot3/design.md) as a separate calibration. It has six development functions, one baseline prompt per function, and five fresh responses per prompt: 30 planned generations. Requested settings remain `gpt-6.1-sol`, medium reasoning, with no inherited conversation.

Completed: **30/30 passes, 595/595 case checks, zero eligible families. Pilot 3 was not run.** Read the [findings](findings.md) and [verification evidence](verification.md).

Before collecting development responses, the manifest freezes all six development functions and twelve distinct held-out functions, their cases and references, canonical clauses, all 42 prompts, validation tests, collection and grading code, and both schedules. The original design and protocol draft remain historical documents. `protocol.json` is the executable calibration protocol; `pilots/pilot3/planned-trials.json` is the full 360-trial schedule whose eligible subset may later be collected.

## Qualification and conditional pilot

A family qualifies only when all five development responses have scored outcomes, one through four pass all cases, and at least one `fail` is independently checked against a valid frozen case and contract. Syntax, extraction, runtime, timeout, and output-limit failures count as unsuccessful responses but cannot alone qualify a family. Missing responses and infrastructure failures leave a cell incomplete. A discovered contract or oracle defect invalidates the family for this round; there is no same-round repair or replacement.

`select_pilot3.py` records all six classifications and the source hashes. At least three families must qualify. If they do, both held-out functions from every qualifying family are retained, preserving their precomputed schedule order. A separate pilot manifest must be frozen before pilot collection. Fewer than three qualifying families means pilot 3 is not run.

The pilot has ten responses per task and format: A prose, B unordered list, and C XML. The formats recover the same ordered clause strings, with identical opening and output instructions. Ten blocks per task contain one response per format; positions are balanced within each task. The seed `20261026` is an arbitrary fixed schedule seed, not a collection date. Primary contrasts are equal-task average B minus A and C minus A success rates; every cell must have ten evaluated responses. These repetitions are not a power calculation.

## Reproduce

Use Python 3.12+ and a running Docker engine. From the repository root:

```sh
python3.12 calibration/round2/run.py self-test
python3.12 calibration/round2/run.py verify --require-complete
python3.12 calibration/round2/run.py grade
python3.12 calibration/round2/select_pilot3.py
```

The CLI does not generate responses. A coordinator dispatches each exact prompt into a fresh native agent with the requested settings, saves the first final message unchanged, and retains session identity, prompt/answer hashes and observation timestamps. No candidate receives feedback, repairs, or a second attempt. Raw records are committed before outcome analysis.

If the gate succeeds, use `pilots/pilot3/run.py` for the pilot's separate freeze, collection, verification, grading and report. A no-launch decision does not create pilot working tasks, protocol, manifest or response records.

## Scope and limitations

The bounded functions combine versioned flows, resource-limited grammars, closures and store snapshots, pickup/delivery scheduling, automaton-constrained walks, and state-dependent edits. Exhaustive small-case oracles and independently checked boundary cases validate expected answers. Reference correctness and passing finite cases do not establish correctness on every valid input.

The unchanged grader uses digest-pinned Python 3.12, a four-second wall limit, half a CPU, 128 MiB memory and a 65,536-byte output limit. Complete reference observation batches are checked against a 48 KiB preparation target. Candidate code executes only inside Docker; goldens remain outside the container. The grader handles ordinary generated code and is not secure against deliberate interpreter tampering.

Fresh native agents retain system instructions, tools and shared filesystem access. The setup cannot establish that references remained inaccessible or that candidates used no tools. Serving revision, sampling temperature/seed and full tool traces are unavailable; requested model settings are not provider-confirmed metadata. Hashes verify the saved artifacts, not an authenticated provider transcript.

Design, implementation, independent session reviews, collection and analysis use AI assistance under user direction. Separate reviewers are not independent human experts. Calibration estimates observed difficulty under one prompt; it cannot estimate prompt sensitivity. Any conditional pilot studies a small, selected convenience sample of related task families and remains exploratory.
