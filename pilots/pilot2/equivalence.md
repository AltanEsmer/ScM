# Pilot 2 semantic equivalence

All nine prompts specify the same three function contracts. A uses connected prose, B uses ordered rules, and C uses a formal contract. Each has the exact same final Python 3.12 standard-library, code-only instruction. No variant supplies examples, implementation hints, or algorithm choices. Indices always refer to the original input order.

| Task / clause | A | B | C |
| --- | --- | --- | --- |
| jobs function and input | `select_jobs(data)`; <=12 integer triples; start < end | Rules 1, 6 | Function contract; input domain |
| jobs feasibility | Half-open intervals; no overlap; touching allowed | Rule 2 | Feasible result |
| jobs empty selection | Empty subset allowed | Rule 2 | Possibly empty I |
| jobs primary ranking | Maximize total profit | Rule 3 | Larger sum preferred |
| jobs second ranking | Minimize job count | Rule 4 | Smaller len(I) preferred |
| jobs final ranking | Lexicographically smallest ascending original zero-based indices | Rule 5 | Ascending original zero-based I; lexicographically smaller preferred |
| jobs output | Ascending index list | Rule 6 | Preferred feasible list I |
| jobs preservation | Do not modify input | Rule 6 | Postcondition |
| path function and input | `match_path(data)`; dictionary; ASCII pattern/text <=30 characters | Rule 1 | Function contract; input domain |
| path match extent | Entire pattern against entire text | Rule 2 | Output iff entire text matched by entire pattern |
| path separator | Slash / | Rule 2 | Interpretation |
| path question mark | Unescaped ? consumes exactly one non-slash character | Rule 4 | Interpretation |
| path single star | Unescaped * consumes zero or more non-slash characters | Rule 5 | Single unescaped * interpretation |
| path multiple stars | Maximal consecutive unescaped run >=2 consumes zero or more arbitrary characters including slash | Rule 6 | Maximal consecutive unescaped run >=2 interpretation |
| path escape | Backslash escapes next character as literal | Rule 3 | Backslash followed by character interpretation |
| path terminal escape | Final backslash literal | Rule 3 | Final backslash interpretation |
| path literals | All other characters literal, including brackets and dot | Rule 7 | All remaining characters literal |
| path output | bool | Rule 8 | bool True iff full match |
| path preservation | Do not modify input | Rule 8 | Postcondition |
| itinerary function and input | `best_itinerary(data)`; dictionary flights/start/goal/time | Rule 1 | Function contract; input domain |
| itinerary flight bounds | <=12 four-element flights; integer times; departure < arrival | Rule 1 | Input domain |
| itinerary city domain | ASCII city strings, including start/goal | Rule 1 | Input domain |
| itinerary first leg | Origin=start; departure >= time | Rule 3 | Feasible route first-index constraints |
| itinerary connections | Origin=previous destination; departure >= previous arrival | Rule 3 | Consecutive-pair constraints |
| itinerary completion | Last destination must equal goal | Rule 3 | Final-index destination constraint |
| itinerary waits and cycles | Waiting/repeated cities allowed | Rule 3 | Waiting/repeated cities permitted |
| itinerary primary ranking | Earliest final arrival | Rule 4 | Smaller final arrival preferred |
| itinerary second ranking | Fewest flights | Rule 5 | Fewer flights preferred |
| itinerary final ranking | Lexicographically smallest original zero-based index sequence in travel order | Rule 6 | Feasible route indices; lexicographically smaller I |
| itinerary start=goal | [] | Rule 2 | Special result |
| itinerary output | Best route as a list of original indices in travel order; None if unavailable | Rule 7 | Preferred route list; None if unavailable |
| itinerary preservation | Do not modify input | Rule 7 | Postcondition |
| all output instructions | Identical final paragraph | Identical final paragraph | Identical final paragraph |

## Case construction and acceptance evidence

`build_cases.py` deterministically writes `tasks.json` in the existing root experiment task shape. Each task has 36 cases. Literal fixtures are independently worked expected values. Remaining inputs use a fixed random seed. Job expected values enumerate all subsets and check pairwise interval compatibility. Itinerary expected values enumerate all subsets, order each chronologically, and check connectivity and time feasibility. Positive flight duration makes chronological order unique for a feasible route, and prevents flight reuse. Path expected values use token reachability over text positions.

References use separate implementations. Jobs incrementally extend compatible selections in end-time order. Paths use escaped regular-expression fragments and fullmatch, with arbitrary-character globstars including ASCII newlines. Itineraries enumerate feasible route extensions. Tests compare every reference result against every literal and generated expected value and assert input preservation. The fixture generator is rerunnable and its exact JSON output is checked.

Literal coverage includes empty inputs, zero and negative profits, endpoint contact, all three ranking levels, original-index output ordering, maximum job count, full matching, empty wildcard consumption, escaped wildcards, escaped backslash, escaped slash, final backslash, triple stars, literal brackets and dot, positive newline consumption by globstar and question mark, maximum path lengths, connection equality, unavailable routes, negative time, identity routes, travel-order indices, and the later-arriving shorter prefix that wins when final arrivals tie.

`tests/test_cases.py` rejects deliberately incorrect implementations. The tests run locally without model calls. This data contribution does not perform collection or publish results. The parent runner owns the three-task, three-variant, five-repetition experiment and sandbox grading.

Local acceptance on Python 3.12 passed six focused unittest checks in approximately 0.21 seconds. Shared-grader-shaped serialized result payloads measured 14,120 bytes for jobs, 5,553 bytes for paths, and 20,454 bytes for itineraries, each below 65,536 bytes. Reference execution over each complete case set measured below 0.01 seconds locally. These measurements cover reference code, not uncollected model answers. Pilot 1 files were preserved, and no commits or model collections were made in this workstream.
