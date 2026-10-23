# Outline for the preliminary Scientific Methods paper

Working title: **Equivalent prompt formats at a correctness ceiling: a bounded code-generation study**

Target: 3 to 6 pages in the IEEE two-column format, excluding the course-required citation screenshot appendix. This file is an argument and section plan, not finished paper prose. Check topic approval and any later course instructions before submission. [Source review](source-review.md) records the ten papers' verified metadata, evidence locations, and transfer limits. Citation occurrence IDs below are stable; each appears once and maps to the same-numbered source and screenshot evidence.

## Abstract. about 150 words, write last

- State the bounded comparison, the frozen design, and the execution endpoint.
- Report 72 of 72 programs passing all retained suites, with 13,068 of 13,068 case checks. Explain that cases are repeated checks of 72 programs.
- State zero observed contrasts and the ceiling limitation. Avoid claims of statistical equivalence or general robustness.

## 1. Introduction. about half a page

- Motivate checking whether presentation changes observed correctness when programming requirements remain recoverably identical.
- Introduce formatting as a measured source of variation in prior few-shot evaluations. **C01 → S01**.
- Research goal: measure observed correctness under equivalent presentations in a fixed code-generation setting.
- One research question: **How do prose, numbered-list, and XML presentations of equivalent programming requirements affect all-case pass rates for `gpt-6.1-sol` with medium reasoning on twelve selected public programming tasks?**
- Contribution: a frozen, balanced comparison with isolated generation and reproducible descriptive analysis. The contribution includes documenting an uninformative correctness ceiling.

## 2. Related work. about three quarters of a page

Organize by intervention and measurement, not a list of ten summaries.

- **Order and answer bias.** Demonstration-order effects motivate explicit control of order, although this study preserves block order and adds no demonstrations. **C02 → S02**. Contextual calibration addresses few-shot answer bias and instability; distinguish that method from this repository's earlier calibration phases. **C08 → S08**.
- **Measurement.** Heuristic scoring can inflate apparent sensitivity in evaluated natural-language benchmarks. **C03 → S03**. Instance-level frameworks motivate retaining task-level outcomes. **C04 → S04**. A likelihood-based sensitivity index measures a different quantity from executable correctness. **C05 → S05**. Sensitivity estimates used as performance proxies also differ from this study's endpoint. **C07 → S07**.
- **Robustness and mitigation.** Consistency learning has been evaluated for lexical perturbations in intent classification and slot filling. **C06 → S06**. Worst-case case-level paraphrase evaluation covers a broader robustness question than three fixed renderers. **C09 → S09**. Latent adversarial training is a mitigation approach outside the present intervention. **C10 → S10**.
- Close with the precise gap addressed here: a small execution-based format comparison, without claiming novelty across all code-generation research. Use the source review for detail and avoid extra citation occurrences unless matching appendix evidence is added.

## 3. Data and methods. about one to one and a half pages

Use the frozen [protocol](../studies/format-study1/PROTOCOL.md), preparation records, and collection records as the study evidence.

- **Units and source.** Twelve source-defined, filtered TACO tasks, six MEDIUM and six HARD. Explain deterministic selection, pre-generation source-defect exclusions, curated retained tests, and public-source contamination risk. These are curated subsets, not an official TACO score.
- **Treatment.** Render the same ordered canonical blocks as prose, numbered lists, or reversibly escaped XML. Explain the recovery check. Syntax and token-length consequences are part of the intervention.
- **Allocation.** Twelve tasks × three formats × two fresh responses = 72 programs. Explain balanced randomized order, frozen seed, and separate fresh threads. The schedule seed does not control model sampling.
- **Collection boundary.** Requested model and medium effort; distinguish backend alias from independent weight attestation. Describe restricted generation containers, relay, local-reference exclusion, and the synthetic live preflight. Do not claim isolation removes pretrained knowledge.
- **Endpoint.** Each raw answer must pass every retained case under frozen Python 3.12 execution limits and exact whitespace-token comparison. No code repair, fence stripping, or response selection. Distinguish failed programs from infrastructure failures.
- **Analysis.** Report successes out of two by task and format. Compute within-task B minus A and C minus A, then average tasks equally. No prespecified significance or equivalence test.
- Add one compact design table and one prompt-format example that preserves the actual block contents. Avoid spending paper space on container implementation details.

## 4. Results. about half a page

Use the saved [findings](../studies/format-study1/results/findings.md) and analysis artifact.

- All 72 scheduled first responses collected once, without missing outcomes or retries. All passed their retained suites, with no execution or infrastructure errors.
- Primary table: twelve task rows, retained cases per response, and A, B, C successes out of two. Each cell is 2/2.
- Report B minus A = 0 and C minus A = 0 for every task and for both equal-task mean contrasts.
- Report 13,068 successful case checks as secondary descriptive evidence. Do not use that count as the number of independent trials.

## 5. Discussion and limits. about three quarters of a page

- Answer the research question at its measured scope: no observed all-case correctness difference among these renderers on these tasks and responses.
- Explain why the ceiling prevents discrimination among formats and leaves failure probabilities poorly characterized. Zero observed difference does not establish equivalence, a universally small effect, or absence of other sensitivity.
- External task authorship and restricted generation improve provenance and prevent configured retrieval of local references. Public task exposure, convenience selection, small inputs, finite fixtures, two repetitions, and unknown model revision remain limits.
- Passing retained tests does not establish full-constraint correctness or runtime quality. Give the protocol's concrete small-input examples if space permits.
- Explain prior phases in one clearly labeled history paragraph or appendix table: custom-task pilots and calibration informed design; the saved-program composite audit generated no new responses; conditional pilot 3 retained its no-launch decision. None is pooled with these 72 responses.
- Future study: freeze a fresh task source, stronger failure-exposing tests, sampling rationale, and analysis before generation. Do not promote a post hoc outcome from the saved answers to a confirmatory endpoint.

## 6. Conclusion and disclosures. about one quarter of a page

- Restate the bounded result and the measurement lesson without claiming a preferred format.
- Disclose AI assistance in design, tooling, preparation, collection, review, and drafting support. Distinguish external problem authorship from AI-assisted study construction and the student's responsibility for the final paper.
- Include reproducibility pointers and relevant data reuse attribution. Keep credentials and private provider information out of the paper.

## References and appendix plan

Use the ten source records in `source-review.md` and the verified bibliography. References count toward the paper's page budget unless course instructions state otherwise. The appendix contains one publisher-version highlighted screenshot per citation occurrence, using the stable occurrence ID and a caption that identifies source, PDF page, and supported claim. Verify that every final citation has evidence and that no screenshot is presented as evidence for a broader claim than its passage supports.
