# Equivalent-format experiment on independent programming tasks

Status: preparation only. No study responses, calibration responses, or live provider canary have been collected. This protocol defines a new study, `format-study1`. It does not change the previous conditional pilot 3 or its no-launch decision.

## Question and scope

Does presenting the same programming requirements in prose, a list, or XML change observed correctness for the requested `gpt-6.1-sol` model with `medium` reasoning on a fixed sample of independently authored programming problems?

The study is exploratory. Its 12 tasks and two responses per task/format are not a power calculation. The design permits a ceiling, a floor, and a null difference. None authorizes changing tasks, prompts, tests, or analysis after inspecting outcomes.

Task authorship is independent of this project's AI-assisted task construction. It does not mean tasks were independently sampled from all programming work, or that the model has never seen them. The source problems and solutions are public, and the model's training cutoff is unavailable. No contamination-free claim is made.

## Task source and selection

Use the test split of [TACO](https://github.com/FlagOpen/TACO), from the [pinned Hugging Face dataset revision](https://huggingface.co/datasets/BAAI/TACO/tree/d593ed0a2becbbc952230bb89be09189bf1056dc). Preserve original problem text, test inputs and expected outputs, supplied solutions, source URLs, and difficulty metadata. The source selection record identifies the shard hash, exclusion rules, ranked eligibility census, and selected IDs.

Select six tasks labeled MEDIUM and six labeled HARD by the dataset. Rank eligible tasks deterministically with a fixed seed, without querying the target model. Eligibility requires ordinary standard-input/output behavior, sufficient supplied tests, and a statically admissible Python standard-library solution. Exclude interactive tasks, special-judge outputs, floating-point comparisons, and tasks whose available provenance does not meet the documented reuse policy. Preserve the publisher's attribution and license notices.

The preparation audit found source cases outside their statements' contracts and tasks with damaged statements or contradictory expectations. Preserve the initial selection and documented whole-task exclusions. Before the final freeze, a whole task may be replaced only for a documented statement or test defect established independently of reference pass rates. Preserve the failed evidence, obtain an independent rule-based review, record the amendment, and take the next eligible task in the original deterministic ranking. Do not repair expected outputs or remove valid-domain cases after observing a reference failure. No replacement may be based on target-model outcomes; none have been collected.

Preserve every original source input and expected output. Apply task-specific, independently reviewed input-domain and expected-output-shape checks to every source case, without computing answers or consulting target-model outputs. Export a separate evaluation-case index map containing every case that passes those checks, in original order. Record each omitted index, reason, and original input/output hashes. Do not rewrite retained inputs, repair expected values, downsample to an arbitrary quota, or omit a valid case because a reference fails it. Each task must retain at least ten cases. This explicitly revises the initial preparation preference to use all supplied cases; the decision occurs before any model generation and is documented in the source audit.

Run supplied reference solutions against every curated evaluation case in the restricted grader. A reference disagreement on a valid retained case blocks readiness until resolved; an ambiguous task cannot silently lose its failing cases. A pre-freeze semantic defect in table-game task 0778 was independently proved from its rules (source case 94 expects `110011`, but the rules imply `110010`). Preserve that whole task and its failed report; its replacement follows the recorded source-defect procedure. This explicitly supersedes the earlier preparation plan to hold all twelve tasks fixed before curated reference validation. It is a data-quality amendment, made before any target-model observations. Do not edit test expectations to make a reference pass. After freezing, an invalid task is reported and excluded from inferential interpretation; it is not silently repaired or replaced. Retain its original files and all collected outcomes. These are curated TACO subsets, not an official TACO benchmark score.

This is a source-defined, filtered convenience sample. Difficulty labels guide diversity and are not measurements of this model's success probability. There is no baseline calibration gate and no requirement that each task first produce mixed outcomes.

## Prompt intervention

For each task, construct one canonical ordered sequence of instruction blocks containing the original question and identical implementation/output requirements. Render three variants:

- A: prose blocks.
- B: list blocks.
- C: XML blocks with reversible escaping.

The automated equivalence check must recover the same canonical block strings from every variant, in the same order. Preserve constraints, examples, code snippets, and numeric values. Do not add hints, demonstrations, role-playing, reasoning requests, or different output requirements to a variant. Inspect all prompt triplets before freezing.

The treatment includes the chosen format syntax and its token-length consequences. It does not isolate every character-level formatting feature separately. All variants request Python 3.12 standard-library code for stdin/stdout with the same extraction and grading policy.

## Allocation and collection

Plan 12 tasks × three formats × two fresh responses, for 72 study generations. Each task has two blocks; each block contains A, B, and C exactly once. Balance format positions across the 24 blocks, using all six permutations four times, and randomize allocation/order with seed `20261022`. Freeze the complete schedule before generation.

Use fresh isolated contexts for every response. Request `gpt-6.1-sol` and `medium` explicitly, disable model fallback, and keep all other controllable settings identical. Do not silently substitute an API model name for this Codex alias. Record requested settings separately from any provider-returned identity. Temperature and sampling seed are not controlled unless the pinned client exposes and records them; the schedule seed is not a model sampling seed.

Collect each first final answer without repair, feedback, follow-up prompts, or answer selection. Do not grade study answers until collection is closed. Preserve empty, malformed, refused, truncated, and interrupted responses and their statuses. Do not regenerate a trial after an ambiguous or interrupted dispatch. A request proven not to have reached the provider may be resumed only under the documented dispatch-state rules, retaining the original failed attempt evidence. Never label a retry as an independent planned repetition.

## Reference isolation

Generation runs in a fresh container with no repository, test, reference-solution, prior-response, home-directory, credential, or Docker-socket mount. The generation image contains only the pinned client and required client files. Its working directories are temporary, its root filesystem is read-only, and it runs unprivileged with dropped capabilities and resource limits.

The generation container has no direct external network route. Its only model-service route is a restricted trusted relay. The relay enforces the requested model/effort and rejects arbitrary destinations and unsafe tools. Real provider credentials remain outside the generation filesystem. Fresh app-server threads disable environment access and fallback, omit dynamic tools and project/skill instructions, and do not inherit earlier conversations.

An offline proof must exercise the real client against a synthetic provider and retain request captures, namespace/network checks, and negative canary tests. It must establish that local reference/test/old-answer canaries are absent from model requests and unavailable inside the generation container, and that direct external access is denied. Offline synthetic responses are test fixtures, not model observations.

A live backend preflight is required before study collection, but is not authorized or run in this preparation task. That later check must use synthetic content unrelated to the 12 tasks, confirm the actual provider route and available model metadata, and preserve the isolation controls. If it fails or cannot establish the required settings, collection stays blocked. Do not weaken isolation or fall back to shared native sessions.

The boundary prevents retrieval of local or remote reference artifacts through the configured execution tools. It cannot remove knowledge already present in model weights or prove provider internals. Public test/reference files can be committed for reproducibility because generation cannot browse the repo or the public internet.

## Outcomes and analysis

The primary outcome is whether the saved program passes every frozen test for its task under the frozen execution limits. Compare whitespace-separated output tokens exactly, with no numeric tolerance, case folding, debug-line deletion, or acceptance of extra output. Use the pinned Python 3.12 image in `grader.py`, a fresh container per test, one CPU, 512 MiB memory, 64 processes, a read-only root and code/input mount, and no network. The ten-second wall-clock limit starts after container creation and includes start/attach overhead; stdout and stderr each have a 1 MiB limit. Mount only the candidate code and input, keeping expected output on the host. Grade the returned text as source without Markdown-fence stripping or code repair. Retain every per-case status. Syntax, runtime, timeout, output-limit, and invalid-format outcomes are unsuccessful responses; infrastructure failure and missing responses are separate incomplete outcomes, not semantic errors.

For each task and format, report successes out of two evaluated responses. Compute B minus A and C minus A within each task, then average the 12 task differences equally. Report the task-level differences alongside the mean. Only compute the complete-design contrasts if all 72 planned responses have evaluable outcomes; otherwise report missingness and descriptive cells without silently changing denominators.

Do not treat test cases as independent model trials, pool task families into one unqualified accuracy estimate, select the best format after inspecting results without labeling the selection, or claim statistical equivalence from equal scores. No confirmatory significance test is planned. With only 12 selected tasks and two repetitions, emphasize observed differences and their limits; do not manufacture precise confidence intervals from case counts. A later confirmatory study would need its own task sampling and power rationale.

The supplied suites predominantly use small inputs. For example, task 0339 has retained arrays of at most 30 elements despite a statement bound of 500,000, and task 0760 at most 20 despite a bound of 100,000. Passing this study does not establish correctness or acceptable runtime across full contest constraints. Inefficient solutions may pass; a ceiling remains possible even for independently authored tasks. No large-input stress suite has been added.

Secondary descriptions may include case pass counts, failure categories, output length, and elapsed execution time. These cannot replace the primary endpoint after a ceiling or null result. Batch-aborted or missing observations do not establish how many unobserved cases would fail.

## Freeze, publication, and deviation policy

Hash selected task/source records, original and curated test inputs and expected outputs, evaluation indices and exclusion reasons, validators, supplied references, canonical blocks, prompts, schedule, protocol, grading and preparation code, isolation controls, and relevant client/image identities. Commit and push the freeze before any study dispatch. Verify the manifest before every collection and grading stage.

Keep readiness evidence separate from model outcomes. The current deliverable is prepared materials plus offline validation. A future live preflight does not count as one of the 72 responses and must contain no study problem. Record every deviation in a new dated artifact; preserve the original freeze. If a change affects the treatment, task set, or scoring contract, issue a new study version before collecting more responses.

All previous pilot, calibration, and audit data remain unchanged. Report AI assistance in selection tooling, protocol preparation, prompt rendering, and review; distinguish external problem authorship from those contributions.
