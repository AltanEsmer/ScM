# Pilot findings, 22 October 2026

All 45 collected responses passed every predefined case. The three introductory phrasings produced no observed difference in this pilot's functional-correctness outcome.

| Task | Wording A | Wording B | Wording C |
| --- | ---: | ---: | ---: |
| Order-preserving deduplication | 5/5 | 5/5 | 5/5 |
| Closed-interval merging | 5/5 | 5/5 | 5/5 |
| ASCII word counts | 5/5 | 5/5 | 5/5 |

The grader completed 330 case assertions across 45 distinct session records. No trial is missing. No generation was repaired, replaced, or retried. The raw first answers and provenance are in [records](../records). The per-trial machine-readable results are in [trials.csv](../results/trials.csv).

## What the pilot establishes

The collection workflow produced a complete sample, and the frozen grader could evaluate every response. Each wording received 15 generations across the three tasks. The observed difference between any pair of wording pass rates is zero percentage points in this sample.

The findings do not establish that wording has no effect in general. Three short introductory paraphrases are a weak intervention, and these tasks appear too easy to distinguish them using pass or fail. Five repetitions per cell and three tasks cannot support a broad equivalence claim. No significance test or causal generalization is reported.

## Source variation

An exploratory inspection after collection found two distinct raw answers for deduplication, five for interval merging, and three for word counts. These counts use exact response hashes, so whitespace and type annotations count as differences. They are not measures of semantic diversity or a prespecified research outcome.

The implementation differences include type annotations, alternative sort keys, explicit counting loops, and `collections.Counter`. Every observed implementation passed the same task cases. Source variation therefore did not translate into a measured correctness difference here.

## Evidence limits

Each session requested `gpt-6.1-sol` with medium reasoning and no inherited conversation. The provider's actual model revision and sampling parameters are unavailable. Full tool traces are also unavailable, and fresh sessions retain system instructions and shared filesystem and tool access. The methodology cannot establish strict context isolation.

The candidate interpreter produces observations for host-side comparison. It is not an adversarially trusted measurement process. All collected source files were read by the coordinator and contain short implementations of the requested functions. The code is retained so others can inspect it.

Finite tests can miss incorrect behavior. Passing 330 assertions is evidence about the fixed cases, not proof of correctness for all inputs.

## Next research decision

Keep this pilot as feasibility evidence. Before the main study, define a new frozen design with harder tasks and a stronger controlled wording intervention. Candidate task requirements could include more interacting edge cases while preserving exact equivalence across prompts. Avoid changing these records or presenting a revised task set as part of this sample.

The next practical deliverable is a revised task-selection rubric and equivalent prompt set, supported by the course's required literature. The literature review and final research paper remain to be completed.
