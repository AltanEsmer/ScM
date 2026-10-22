# Calibration verification

The test contracts were committed in `55220e9`, followed by implementation and the six-task pool in `0b37b24`. The design was frozen in `09521fa9808d065a8472721dcd37567a62369d35` before the first model dispatch. The fixed rule classifies only complete cells of three evaluated responses: one or two all-case passes are eligible, three is ceiling, and zero is floor. Missing or infrastructure-affected cells cannot qualify.

## Preflight

Independent review found graph batches exceeding the unchanged 65,536-byte output limit. Raw JSON size understated the runner's typed input observations. The batches were reduced before freezing, retaining hard certified cases, and tests now check the complete serialized observation. The final graph payloads are 46,014 and 44,799 bytes. A Docker run exposed the original overflow; no research responses were collected using those invalid batches.

Review also found a missing lexical-parameter-shadowing fixture. A literal case and reversed-binding-order mutant were added before collection. No actionable review findings remained before freeze. All 27 calibration tests passed. All six curated reference functions passed the real Docker grader: 34 edit-distance, 35 circulation, 36 arborescence, 28 grammar, 28 route and 33 interpreter cases. These 194 inputs imply 582 planned case evaluations across three generated responses per task. Reference batch runs took about 0.24–0.55 seconds including Docker startup on this host, below the four-second timeout.

Small graph goldens use exhaustive independent enumeration; large graph cases include constructed optima with certificates. Short edit cases use explicit edit-script search; three longer random edit pairs use the same unrestricted-distance reference for their expected values and are not independently certified. Grammar and route cases combine worked literals with independent enumeration on bounded instances. Interpreter cases have literal expected values and a separate substitution-based oracle. These checks improve fixture confidence without proving the grader or entire input domain correct.

The five separate uncertainty-helper tests pass against exact edge formulas and known binomial interval values. Its outputs are illustrative iid-binomial calculations, not a new inferential analysis of the earlier pilots.

## Preservation and evidence limits

The root pilot and pilot2 both pass complete verification. Their frozen source, cases, prompts and records are unchanged. Calibration uses the unchanged root grader and pinned Docker image. Fresh native model sessions still have tools/system context/shared filesystem access. The saved provenance contains requested settings, unique session paths, hashes and coordinator observation timestamps, not an authenticated backend model transcript. Full candidate tool traces and model sampling controls are unavailable.

## Completed collection and grading

All 18 first responses were saved in unique fresh sessions, with zero missing or interrupted trials. Raw evidence was committed at `2949e76` before grading. The first full grading run evaluated every response successfully: 18 all-case passes, 582/582 successful case checks, no exclusions, and six ceiling classifications. No family qualified under the frozen rule. There is no failure diagnosis or corrected-answer run because no candidate failed.

The calibration-only collection used a maximum of two concurrent candidate sessions. Input hashes continue to match the precollection manifest. The collection coordinator recorded the first returned final text without adding a terminal newline, repair, retry or follow-up. These are coordinator observations, not provider-authenticated transcripts.

## Final acceptance and publication

The complete regression checks passed 60 tests: 12 root-grader/pilot tests, 16 pilot2 tests, 27 calibration tests, and five uncertainty-helper tests. The saved [test log](results/tooling-tests.txt) records the runs. Syntax compilation passed for the calibration driver, builders, pool modules and uncertainty helper. No dedicated static type checker or lint configuration is claimed; whitespace checks pass.

A fresh `git clone --no-local` into a temporary directory passed complete verification for the root pilot (45 records), pilot2 (45), and calibration (18), without ignored working files. Both earlier experiments remain byte-for-byte unchanged apart from the root README navigation. Calibration frozen inputs match `09521fa` exactly.

Final independent review found no actionable issues in integrity, chronology, classification, numeric illustrations or narrative claims. The completed findings, report-strength assessment and machine-readable third-pilot draft agree: six observed ceilings, zero eligible families, and a conditional design with no third-pilot collection. The review used another agent session in the same model family. It does not supply independent provider attestation or human validation.

The Git remote was verified as `https://github.com/AltanEsmer/ScM.git`. Only experiment artifacts, analysis tooling and documentation are added; ignored course materials, credentials and scratch files are excluded.
