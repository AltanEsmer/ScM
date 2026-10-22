# Methodology for the first pilot

## Research question

How does introductory instruction wording affect functional correctness on three small Python tasks when the task specification stays identical?

This is an observational pilot using fresh conversation contexts. It is intended to verify the collection and scoring workflow and detect obvious ceiling effects before a larger study.

## Design

The tasks are order-preserving integer deduplication, closed-interval merging, and ASCII word-frequency counting. Each has three introductory phrasings. The specification and output instructions remain byte-identical within each task. Each task and wording combination has five repetitions, giving 45 planned generations.

The schedule was shuffled with seed 20261022. Dispatch follows the saved schedule in waves of at most three concurrent candidates. Completion order can differ. Each generation uses a new native subagent with no parent conversation history. The exact prompt text is the full assignment, with no research description, tests, reference answers, previous outputs, or feedback appended.

The requested model is `gpt-6.1-sol` and the requested reasoning effort is `medium`. The native tool accepts these settings. The provider's actual weights, backend revision, sampling temperature, and random seed are not exposed. Record them as unavailable rather than infer values. Native session identifiers are agent paths returned by the tool, not provider request IDs.

A preparatory CLI request asking for `READY` failed because the installed CLI rejected this model for the account. That request was not a programming trial. No programming trials were run with a substitute model. Collection therefore uses native subagents rather than the CLI.

## Provenance and context limits

The coordinator records dispatch and completion observation timestamps, the agent path, requested settings, exact prompt and answer hashes, and the raw first final answer. Dispatch timestamps record when an ordinal is queued, shortly before its tool call. Completion timestamps record capture of the returned final message. Neither is a provider-side generation timestamp. Responses are copied from returned final messages without correcting code or removing Markdown fences. No failed answer is replaced.

No-history mode prevents inheritance of this conversation. It does not establish a blank system context, disable tools, or deny access to the shared filesystem. Full tool-event traces are not available to this coordinator. The evidence cannot establish that every candidate avoided tools or filesystem reads. The prompts ask for source code only. Claims are limited to this native-session setup.

Records are stored once and checked by hashes. This provides integrity checks within the repository. It is not cryptographic provider attestation, and a person with write access could rewrite both evidence and hashes.

## Scoring

The primary outcome is whether a generation passes all predefined cases. Report counts separately for each task and wording. Each case requires an exact expected value and recursively correct JSON types. Integer values cannot be replaced by Boolean values. The original input must remain unchanged. Deduplication must return a distinct list.

The extractor accepts bare Python source or one complete Python code fence without surrounding prose. Other text is parsed unchanged. Syntax errors, runtime errors, timeouts, and incorrect results are unsuccessful generations. Missing trials and infrastructure errors remain separate and do not silently enter the success denominator.

Generated Python runs in a digest-pinned Docker container with no network, a read-only filesystem, a non-root user, and resource limits. Expected values and reference solutions stay on the host. The host compares returned observations and never accepts a candidate-declared pass status. The runner shares the candidate interpreter. All returned observations, including values, types, input mutation, and identity, could be fabricated by deliberately malicious code that tampers with the interpreter or result transport. This grader targets ordinary generated solutions, not an adversarial competition.

## Analysis and limits

Report descriptive counts and per-task wording differences. Do not treat 45 generations as 45 independent tasks. With three easy tasks and five repetitions per cell, broad generalization and claims of equivalence are unsupported. A 100 percent pass rate would indicate a ceiling effect in this sample, not prove that prompt wording never matters.

The fixed finite cases cannot establish correctness for every possible input. Introductory paraphrases are a narrow intervention. The pilot does not test ambiguous specifications, examples, formatting changes, multiple models, or difficult programming problems. It contains no literature-backed causal claim and is separate from the final course paper.

If the pilot leads to changes, freeze a new experiment before collecting main-study data. Do not alter these prompts or cases after looking at their outcomes.
