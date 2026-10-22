# Prompt sensitivity pilot 2

| Task | Variant | Collected | Evaluated | Pass | Failure | Infrastructure | Not evaluated | Missing |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| select_jobs | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| select_jobs | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| select_jobs | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| match_path | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| match_path | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| match_path | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| best_itinerary | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| best_itinerary | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| best_itinerary | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |

Functional pass denominator is Evaluated. Missing, infrastructure failures, and not evaluated trials are excluded.
Candidate execution errors count as functional failures. Collected includes infrastructure failures and not evaluated trials.
Interrupted dispatches are included in Missing. Five repetitions per cell provide limited evidence. All-pass results do not establish wording invariance.
Requested model and reasoning are not provider-confirmed metadata. Full tool traces are unavailable.
Fresh no-history agents retain system instructions and filesystem/tool access.
Host scoring compares returned observations. Deliberate candidate interpreter tampering can fabricate all observations.
The threat model is ordinary generated code, not a fully malicious candidate.
