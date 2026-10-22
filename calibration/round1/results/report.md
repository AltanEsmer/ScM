# Baseline task-pool calibration round 1

| Task | Variant | Collected | Evaluated | Pass | Failure | Infrastructure | Not evaluated | Missing | Classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| damerau_distance | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |
| min_cost_circulation | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |
| minimum_arborescence | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |
| min_parse_cost | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |
| min_resource_route | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |
| eval_lexical | B0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | ceiling |

Baseline calibration only. This run does not compare prompt variants.
Selection rule: Exactly three evaluated responses required. 1/3 or 2/3 all-case passes: mixed, eligible for priority family selection; 3/3: ceiling, exclude from primary selection; 0/3: floor, diagnose specification/oracle and failure before any future simplification. Missing/infrastructure/not-evaluated: incomplete, no classification. No model retries or outcome-driven edits. If no mixed family emerges, do not pretend calibration succeeded: document floors/ceilings and make third pilot conditional on a new separately frozen calibration.
Eligible means one or two functional passes among three evaluated trials. Three passes is ceiling; zero passes is floor. Otherwise classification is incomplete.
Functional pass denominator is Evaluated. Missing, infrastructure failures, and not evaluated trials are excluded.
Candidate execution errors count as functional failures. Collected includes infrastructure failures and not evaluated trials.
Interrupted dispatches are included in Missing. Three repetitions provide limited calibration evidence.
Requested model and reasoning are not provider-confirmed metadata. Full tool traces are unavailable.
Fresh no-history agents retain system instructions and filesystem/tool access.
Host scoring compares returned observations. Deliberate candidate interpreter tampering can fabricate all observations.
The threat model is ordinary generated code, not a fully malicious candidate.
