# Conditional third-pilot design

Status is **not ready and not collected**. Calibration round 1 produced 18/18 passing generations and 582/582 passing case checks. All six task cells are ceilings under its frozen rule. There are zero eligible families. [The calibration report](../../calibration/round1/results/report.md) provides the observed counts. No third-pilot response or further development-calibration response has been collected.

This draft proposes a separate development calibration and a conditional format-comparison pilot. It does not reinterpret the completed calibration, weaken its selection rule, or guarantee that a future task or format produces failures. Increasing the size of familiar algorithms alone did not establish useful difficulty variation.

## Gate collection on a separate development calibration

Develop six new composite function contracts from the registry below. Before collecting any response, complete their public schemas, bounds, semantics, baseline prompts, finite cases, references, independent oracle checks, dispatch schedule, and manifest. Complete and hash the twelve paired held-out contracts and their cases at the same time. Keep all held-out material unavailable to development candidates to the extent the collection environment supports that restriction. These are new experiments with new identifiers. Preserve the completed pilots and calibration unchanged.

Use one neutral baseline prompt per development contract and five fresh responses, for exactly 30 planned development generations. Keep `gpt-6.1-sol`, medium reasoning, and the same common source-code output instructions. Do not compare formats during calibration. No response receives feedback, repairs, or another attempt.

A family qualifies only if all five responses are collected and scored without infrastructure failure, exactly one through four responses pass every case, and at least one unsuccessful response has a valid observed functional mismatch. For this gate, a functional mismatch is the grader's `fail` status on a valid frozen case, including a wrong value, wrong type, or input mutation. Syntax, extraction, runtime, timeout, and output-limit errors still count as unsuccessful generations, but those errors alone cannot qualify a family. Infrastructure errors and missing responses leave its cell incomplete. The gate does not infer semantic difficulty from execution-limit or formatting artifacts.

Before classification, verify every qualifying mismatch against the frozen contract and independently checked expected value. A discovered contract, case, oracle, or runner defect invalidates the affected family for this round. Document the defect. Do not edit it into eligibility or recollect it in the same round. Reviewers may diagnose the result but cannot waive these criteria. This rule is deliberately conservative and must be frozen with the actual development protocol.

Include both held-out contracts from every qualifying family. Do not select only promising contracts or the most favorable failure rates. Three through six eligible families give six through twelve held-out contracts. If fewer than three families qualify, do not launch pilot 3. Report an unsuccessful development calibration. Any later calibration requires a separate rationale, bounded new design, and freeze. There is no automatic cycle of task changes until an effect appears.

Selection after exploratory calibration limits generalization to the selected families. The held-out contracts have different requested behaviors, not new random inputs for development functions. Their actual difficulty remains unknown. All-pass held-out results remain a possible and reportable outcome.

## Draft registry of distinct contracts

The following registry fixes the intended differences between development and held-out tasks. It is a design artifact, not an executable specification. Every row still needs complete valid-input schemas, operation semantics, bounds, return types, cases, and independent oracle review before freeze. No task is approved for collection merely by appearing here. Bounds must permit a correct implementation to run with substantial headroom under the frozen grading policy.

| Family | Development contract | Held-out contract 1 | Held-out contract 2 | Independent oracle direction |
| --- | --- | --- | --- | --- |
| F1. Versioned network optimization | `versioned_circulation_costs` returns minimum circulation cost at every node of a version tree after that node's bounded-capacity update to its parent snapshot. Versions branch and earlier snapshots retain their meaning. | `inventory_transfer_cost` minimizes a time-expanded transport plan with dated supplies, dated demands, carry capacity, and storage cost. | `single_failure_costs` returns the optimum under each independently disabled arc of a lower-bound circulation, including infeasibility. | Enumerate all bounded flow assignments on tiny instances. Validate large optima with feasible primal flows and residual potentials. Validate infeasibility with independent cut certificates. Rebuild each version or failure scenario independently when checking it. |
| F2. Grammar derivations with a resource budget | `budget_parse_cost` minimizes rule cost for an exact input string while each rule occurrence spends positive integer resource under a total budget. Epsilon and recursive rules remain legal. | `bounded_derivation_count` counts distinct derivation trees within the resource budget modulo a fixed prime. Rule occurrences and duplicate rule identities distinguish trees. | `budget_grammar_edit_cost` minimizes the edit distance from an observed string to any yield of a derivation within the rule-resource budget. | Enumerate finite trees under the positive resource budget for tiny cases. Cross-check resource-indexed chart computation against an independently normalized grammar algorithm. Counting and minimum-cost oracles need separate checks. |
| F3. Lexical closures with persistent store | `store_program_result` evaluates a lexically scoped language with allocated cells and explicit immutable store snapshots. Return the final scalar and observable store under a defined cell-order policy. | `forked_store_observations` evaluates named branches from earlier store snapshots and returns branch observations. Updates remain confined to each branch while closures retain the specified lexical bindings. | `bounded_store_equivalence` compares two programs over a declared finite input domain using final values and observable stores as the equivalence criterion. | Cross-check a closure/environment/store evaluator against a substitution evaluator with an explicit store. Enumerate the bounded input domain for equivalence. Independently test allocation, aliasing, and snapshot behavior. |
| F4. Transport scheduling with capacity and time | `pickup_delivery_cost` finds the least-cost single-vehicle route meeting pickup-before-delivery, capacity, service-time, and time-window constraints. Waiting is allowed. | `fleet_assignment_cost` assigns all requests to a bounded fleet and schedules each vehicle, minimizing total cost under per-vehicle constraints. | `reward_delivery_selection` chooses which requests to serve and a feasible route under a travel budget, maximizing served reward. | Exhaustively enumerate request assignments and visit orders on tiny cases. Independently simulate route feasibility and objective values. Use exact host optimization with checked certificates or constructed bounds for larger cases. |
| F5. Resource walks accepted by an automaton | `automaton_route_cost` minimizes signed monetary cost under positive resource use while edge labels drive a finite automaton. A valid ending must satisfy both the graph goal and accepting state. | `accepted_walk_counts` returns the number of accepted walks at each exact resource use, modulo a fixed prime. Distinct edge occurrences distinguish walks. | `budget_route_strategy` computes the least worst-case cost in a turn-based graph where an adversary controls designated vertices, subject to resource exhaustion and automaton acceptance. | Enumerate bounded walks for tiny counting and cost cases. Enumerate finite strategies for tiny games. Independently compute generic expanded-state transitions, then use exhaustive or game-specific evaluation. |
| F6. Structured edits and finite-state constraints | `constrained_edit_cost` finds the minimum positive-cost edit script transforming a string into an output accepted by a finite-state validator, with bounded output length and explicit edit-mode state. | `optimal_edit_script_count` counts distinct minimum-cost scripts under a fixed operation-count limit and finite alphabet. Script identity and repeated edits must be specified explicitly. | `joint_text_repair_cost` repairs two observed strings to one common validator-accepted output, minimizing their combined edit costs under an output-length bound. | Enumerate bounded scripts or output strings independently on tiny cases. Cross-check shortest-path state expansion with a separately authored dynamic program. Positive operation costs and explicit bounds exclude infinite script counts. |

These are six composite directions, not a claim of six independently measured difficulty levels. Persistent stores, multi-vehicle scheduling, counting, and adversarial strategies may be too hard or too easy. The gate records that outcome. Companion contracts can also differ substantially in difficulty from their development contract.

## Isolate format in the third pilot

For each retained held-out contract, author one canonical ordered list of semantic clauses. Create three prompts mechanically from those same clauses.

- A joins the clauses as prose paragraphs.
- B presents the same clauses as an unordered list.
- C places each clause inside an XML `clause` element, using escaping that decodes to the canonical text.

Every clause retains its exact words, punctuation, and position. A machine check must recover identical ordered clause strings from all three forms. Keep the opening instruction and final source-code output instructions byte-identical across variants. Use equal examples in equal positions, or omit examples from all variants. Include no asymmetric hints, algorithm names, examples, motivational language, or competence claims.

This contrast changes presentation, delimiters, and markup. Its token count may differ as part of the format intervention. It does not isolate every visual property of formatting. Defer lexical paraphrasing to a separate experiment rather than combining it with this contrast.

## Fix the generation plan before collection

Use three variants and ten fresh responses per variant for each of six through twelve retained contracts. The planned third-pilot count is therefore 180 through 360 generations. These repetitions are a feasible design choice, not a power calculation or a guarantee of detecting an effect.

Use ten dispatch blocks per task, with one response for each variant in every block. Freeze a seeded schedule that randomizes task order and balances variant positions to differ by at most one within each task. Dispatch in that order with at most three concurrent sessions. Save the first returned final answer unchanged, including invalid output. No repairs, additional attempts, optional stopping, or adaptation to interim outcomes. Complete the planned schedule before analyzing format differences.

Retain the requested model, reasoning, no-history setting, exact prompt hash, response hash, schedule position, session identity, and coordinator observation timestamps for every response. Requested settings remain `gpt-6.1-sol` and medium reasoning. Do not silently substitute another model or effort level. Record unavailable backend revision, sampling seed, temperature, and full tool-event evidence as unavailable.

Fresh no-history sessions still retain system instructions, tools, and shared filesystem access in the current environment. This cannot establish isolation from reference solutions or earlier candidate code. Better access isolation, authenticated transcripts, and independent human oracle review would support stronger confirmatory claims. Without them, label results as a controlled pilot in the documented native-session setup.

## Freeze the checks and classify outcomes

Freeze all task contracts, canonical clauses, rendered prompts, references, goldens, generators, mutation checks, schedule, model settings, scoring rules, execution limits, and analysis before the first relevant generation. Hash the exact grader and digest-pinned runtime image. Keep expected values and references outside the execution container.

Every task needs an independent oracle strategy and targeted cases for each interaction introduced by its contract. Before freeze, verify valid-input membership, exact return types, input preservation, oracle agreement, known incorrect implementations, complete typed observation size, and actual Docker runtime. A human reviewer who did not author the reference should independently inspect the contracts and selected goldens before any confirmatory interpretation.

The current grader has a four-second wall limit, half a CPU, 128 MiB memory, and a 65,536-byte combined-output limit. Reuse it only if all correct references have measured headroom for complete task batches. Target at most 48 KiB for typed observations. If these policies need to change, define and justify that change before any collection and use it equally across variants. A larger algorithm is not a useful difficulty manipulation if all correct answers hit the runner limit.

The generation outcome is binary. It passes only if every predefined case passes. Wrong outputs, incorrect types, input mutation, syntax errors, invalid format, runtime errors, timeouts, and output-limit failures count as unsuccessful generations. Case counts and failure categories are diagnostic outcomes only.

Missing answers and infrastructure failures remain separate from functional failures. A documented infrastructure repair may regrade the same immutable answer under unchanged frozen semantics. It cannot request a new model response or reveal feedback to that response. If any planned task/variant cell remains incomplete, report available descriptive counts and mark the primary planned comparison incomplete. Do not silently drop the task or treat exclusions as successes or failures.

## Compare tasks rather than case checks

For task `t` and variant `v`, let `p[t,v]` be the number of successful generations divided by ten, provided all ten have valid scored outcomes. With `T` retained held-out contracts, the two primary contrasts are:

- `D_BA = sum_t(p[t,B] - p[t,A]) / T`.
- `D_CA = sum_t(p[t,C] - p[t,A]) / T`.

Report both signed differences in percentage points, the per-task rates, denominators, and failure categories. Equal weighting prevents tasks with larger case batches from dominating. Because each included family contributes exactly two contracts, task averaging also gives each retained family equal total weight. C minus B and within-task case counts are secondary descriptive results.

An individual fresh response is a generation unit. Task contracts are the units over which format differences are averaged. The two contracts in each family may share dependencies. Hundreds of generation trials and thousands of case checks do not create hundreds of independent task samples. The retained contracts form a selected convenience sample, not a random sample of programming work.

Optionally report a preregistered exploratory bootstrap that resamples entire task contracts while retaining all variants and responses within a sampled contract. Also examine resampling the paired contracts together by family. With only six through twelve task contracts and three through six families, either interval is unstable and cannot establish population effects. Report the resampling method and seed. Do not use case-level bootstrap, claim equivalence from an all-pass result, or attach an unearned significance or power claim.

If no format difference appears, report the observed zero contrast and any ceiling or floor pattern. If a difference appears, report it with its limited scope and the full task results. Neither outcome licenses retrospective task replacement or another prompt form in this pilot.

## Conditions still required

The registry is draft-only. Full public contracts, independently verified oracles, human review, actual execution measurements, a development-calibration freeze, its 30 responses, and at least three eligible families do not yet exist. The twelve held-out contracts must be finalized and frozen before those development outcomes are inspected. A separate, final pilot-3 freeze must then record the mechanically retained subset, exact prompts, schedule, and analysis before collection.

No step in this document launches calibration or pilot 3. The current result remains six ceilings and zero eligible families.
