# Prompt sensitivity pilot

| Task | Variant | Collected | Evaluated | Pass | Failure | Infrastructure | Not evaluated | Missing |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deduplicate | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| deduplicate | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| deduplicate | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| merge_intervals | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| merge_intervals | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| merge_intervals | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| word_counts | A | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| word_counts | B | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| word_counts | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |

Functional pass denominator is Evaluated. Missing, infrastructure failures, and not evaluated trials are excluded.
Candidate execution errors count as functional failures. Collected includes infrastructure failures and not evaluated trials.
Five repetitions per cell provide limited evidence. All-pass results do not establish wording invariance.
Requested model and reasoning are not provider-confirmed metadata. Full tool traces are unavailable.
Fresh no-history agents retain system instructions and filesystem/tool access.
Host scoring compares returned observations. Deliberate candidate interpreter tampering can fabricate all observations.
The threat model is ordinary generated code, not a fully malicious candidate.
