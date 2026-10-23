# Collection and grading verification

The synthetic live canary returned `SCM_LIVE_CANARY_OK` with requested and reported model `gpt-6.1-sol`, `medium` reasoning, `tools: []`, and the frozen image ID. Its record is [`../runs/live-canary.json`](../runs/live-canary.json). The canary did not contain a study task.

The collection gate in [`grade_saved.py`](grade_saved.py) checked all 72 dispatch and generation files before any answer was graded. It checked the frozen manifest, prompt and answer bindings, requested and reported settings, image and source hashes, and unique thread IDs. It passed with 72 distinct threads. Dispatch timestamps followed the frozen sequence. The driver then ran the unchanged [`../grader.py`](../grader.py) with three case workers within one response at a time. It saved create-only attempt and result files for each response and bound each case result to the frozen source index and input and expected-output hashes.

The frozen [`../analyze.py`](../analyze.py) accepted all 72 outcomes. Independent reconciliation counted 13,068 case results, all with status `OK` and `passed: true`; there were no unavailable outcomes. Each variant had 24/24 all-case successes. Both mean contrasts were zero. The analysis is saved in [`analysis.json`](analysis.json).

Focused checks passed before grading: six synthetic tests for the collection gate and the 196-artifact freeze verification. The independent reviewer reconciled all 72 collection, grade, and analysis records, including every saved case's source index, hashes, expected tokens, and aggregate count. The reviewer used the same model family as the implementation and did not provide cross-family validation.

The collection and grading scripts preserved the frozen study inputs and scoring code. The orchestration driver was added under `results/` after the freeze; it verifies and invokes the frozen grader but does not change the test set, comparison rule, or primary outcome.
