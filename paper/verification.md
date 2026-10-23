# Verification of the preliminary paper package

Verified 23 October 2026. This package contains ten peer-reviewed proceedings sources, ten planned manuscript citation occurrences, ten highlighted publisher-page PNGs, one ten-page appendix, a bibliography, a source review, and an outline. It contains no new model responses and changes no experiment artifacts.

## Source acceptance and publication

Each source's title, author order, venue, year, and pagination were matched to its publisher proceedings record and PDF. The local ignored cache contains the publisher PDFs and HTML downloaded from the URLs in `evidence/sources.json`. Source hashes bind that review to specific downloaded versions. This is verification of published records and claim passages, not replication of the authors' experiments.

The sources are accepted main-conference or Findings papers, not unreviewed preprints or workshop posters. The official proceedings entries are linked per paper in the source review. The review-status basis also includes these primary venue records.

- S01 is in the ICLR 2024 conference proceedings. The [official call](https://iclr.cc/Conferences/2024/CallForPapers) describes double-blind official reviews and acceptance decisions.
- S02 is in ACL 2022 long-paper proceedings. The [chairs' review-process account](https://2022.aclweb.org/post/acl-2022-chairs-blog-post-about-paper-commitment-and-anonymity-period.html) documents ARR reviews and meta-reviews.
- S03 and S10 are in EMNLP 2025 main proceedings. The [official call](https://2025.emnlp.org/calls/main_conference_papers/) describes the ARR review and conference selection process.
- S04 and S05 are in Findings of EMNLP 2024. The [program chairs' acceptance account](https://2024.emnlp.org/program/) explains reviewed Findings acceptance separately from main-conference acceptance.
- S06 is in Findings of EACL 2024. The [official conference site](https://2024.eacl.org/) documents ARR-reviewed commitments and separate Findings acceptance, and links the archival proceedings.
- S07 is in NAACL 2024 long-paper proceedings. The publisher record identifies the main long-paper volume. The [NAACL acceptance account](https://2024.naacl.org/blog/acceptance/) documents ARR reviews and main-conference selection.
- S08 is in ICML 2021, PMLR volume 139. The [official call](https://icml.cc/Conferences/2021/CallForPapers) specifies double-blind review for main-conference papers.
- S09 is in NeurIPS 2024 main proceedings. The [reviewer guidelines](https://neurips.cc/Conferences/2024/ReviewerGuidelines) describe double-blind review and decisions.

The PMLR landing record names Zihao Zhao, while its PDF prints Tony Z. Zhao. The bibliography preserves the official PMLR export and the source review records the discrepancy. ICLR and NeurIPS proceedings ranges differ from internal conference-PDF pagination. Evidence captions identify the actual PDF page and printed locator.

## Evidence and result checks

The renderer matched every exact highlight fragment against the selected publisher page before rendering. Original PDF bytes were checked against their saved SHA256 hashes. Each screenshot preserves the publisher page text, authors, title, and pagination, with locally applied yellow highlights. The appendix adds provenance and a bounded supported-claim caption.

All ten final appendix pages were rendered and visually inspected as a contact sheet for missing pages, cropped content, overlapping captions, and missing highlights. Selected pages were also inspected at enlarged resolution. The separate reviewer inspected source text, bibliography mappings, source hashes, and screenshot traceability. That review caught under-highlighted passages for four claims. Expanded highlights were regenerated and matched against the publisher text before completion. Review involved separate agents in one model family, not independent human review.

The outline's study statements were checked against the frozen protocol and results. They retain 72/72 programs, 13,068/13,068 repeated case checks, two responses per task and format, zero mean contrasts, and the ceiling limitation. The earlier phases are not pooled with the new study. All 196 frozen experiment artifacts still pass verification.

Reproduce the checks from the repository root.

```sh
python -m pip install -r paper/requirements.txt
python paper/verify_evidence.py
python3 studies/format-study1/prepare.py verify
git diff --check
```

The evidence check passes for ten source records, exactly ten citation occurrences, consistent provisional reference order, ten screenshot hashes, literal matches against all cached source passages when available, ten appendix pages with matching citation labels, and ten syntactically parseable bibliography entries. The PDF contains raster publisher pages, so selecting its source article text is not expected to work; use the PNGs or original publisher PDFs for close reading.

## Remaining work

This is a focused literature package, not a systematic literature review or a finished paper. Draft the IEEE manuscript, review the sources personally, add the appropriate dataset citation and attribution, and reconcile every final citation occurrence with the appendix. The outline's current ten citations are covered. New or broader claims need new evidence. Confirm topic agreement and any course instructions issued after the two supplied lectures. The detailed AI disclosure must travel with the final paper.
