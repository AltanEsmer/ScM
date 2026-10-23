# Preliminary paper materials

The [compiled preliminary paper](output/preliminary-paper.pdf) contains four IEEE pages including references, followed by a twelve-page citation appendix. The [LaTeX source](manuscript/main.tex) follows the [outline](outline.md). The working title is **Equivalent prompt formats at a correctness ceiling: a bounded code-generation study**. The [source review](source-review.md) checks ten peer-reviewed proceedings papers against publisher records and PDFs, with a supported claim and transfer limit for each. This is a focused source selection, not a systematic review.

The [bibliography](references.bib) contains ten publisher-derived entries. Publisher abstracts were omitted from the entries. Individual metadata exports are retained in `evidence/`. The PMLR author-name difference for S08 is documented in the source review. No source is included solely on the basis of an arXiv preprint.

The [annotated citation appendix](output/citation-appendix.pdf) has ten pages. Each page identifies the source, provisional reference number, citation occurrence, publisher PDF URL, file page, and printed pagination. It contains a rendered publisher page with a yellow highlight on the planned citation passage. The [evidence index](evidence/README.md) links the individual PNG screenshots. These are rendered screenshots of the publisher PDFs, not reconstructed text or screenshots of preprint copies. Highlights are added locally; source PDF bytes remain unchanged in the ignored download cache.

The outline assigns one occurrence per paper. C01 through C10 are persistent occurrence identifiers, not final IEEE reference numbers. The provisional numeric reference tags follow first appearance in the current outline. The current manuscript preserves that order. It adds C11 for the first-party dataset record as reference [11], with its own highlighted evidence. This additional record is not counted among the ten peer-reviewed papers. When editing or reordering the manuscript, reconcile the reference tags with the bibliography. Every added citation occurrence, including another citation to an existing paper, needs its own highlighted evidence entry. The source review is a working note, not part of the submitted paper. Its additional source discussion does not substitute for evidence for new manuscript claims.

## Course requirements and remaining work

The first two locally supplied Scientific Methods lectures specify a 3 to 6 page IEEE two-column LaTeX paper, at least ten peer-reviewed references, detailed AI disclosure, and an annotated screenshot appendix outside the page limit. Lecture 2, slides 63 and 64, specifies publisher versions and a screenshot for every citation occurrence. The lecture files are ignored locally. The preliminary deadline stated in Lecture 1 is 4 December 2026. Confirm topic agreement and later course updates.

This package now includes a compiled IEEE preliminary draft. It remains an AI-assisted draft for author review, not a claim that personal source verification or submission approval has occurred. Review the argument and sources, revise the text in your own words, and retain the citation-to-evidence mapping. The core result remains 72/72 programs and 13,068/13,068 repeated case checks, with zero observed task-level contrasts. A correctness ceiling does not establish statistical equivalence or general prompt insensitivity.

## Rebuild the evidence

Install the pinned dependencies with `python -m pip install -r paper/requirements.txt`. From the repository root run `python paper/build_evidence.py`. Missing publisher PDFs are fetched into ignored `work/paper-sources/`. Each download must match the frozen SHA256 in `evidence/sources.json` before rendering. A publisher revision will fail that check and require an explicit evidence review. The script generates the ten PNGs, a render manifest, and the appendix. PDF container metadata can change between builds, so the generated appendix hash is recorded on each build rather than promised to be byte-identical.

The source manifest records exact highlight text, publisher URLs, page locations, access date, and PDF hashes. The render manifest records screenshot hashes and highlight geometry. `python paper/verify_evidence.py` checks citation coverage, file integrity, and appendix page count offline. Initial verification also matched each highlighted passage against the cached publisher PDF and visually inspected all ten pages. See [verification](verification.md).

The project license does not relicense third-party article pages. Publisher and author rights remain with their owners. The screenshots are attributed academic citation evidence, with no edits to the underlying text. Full publisher PDFs and lecture files are excluded from Git.

## Build and verify the manuscript

The source uses the standard `IEEEtran` conference class and `IEEEtran` bibliography style, with A4 paper and ten-point type. No custom margins or reduced body font are used. The main paper includes results, limitations, earlier-phase context, detailed AI disclosure, and eleven references. Its four pages are followed by an appendix cover, the ten existing publisher evidence pages, and the official dataset-card screenshot page.

Install Tectonic from its [official distribution](https://tectonic-typesetting.github.io/book/latest/installation/) and install `paper/requirements.txt` into your Python environment. From the repository root run:

```sh
python paper/build_manuscript.py --tectonic /path/to/tectonic
python paper/verify_manuscript.py
python3 studies/format-study1/prepare.py verify
```

The builder regenerates the results table from the saved analysis and retained fixture records, compiles the LaTeX and bibliography, and saves `paper/output/preliminary-paper.pdf`. Temporary TeX files and logs go to ignored `work/paper-build/`. The tracked `manuscript/build-record.json` binds the compiler version, source inputs, evidence PDFs, and compiled output to hashes. The current build uses Tectonic 0.17.0 and IEEEtran 1.8b. Tectonic may download TeX support files on first use. The compiler is not part of the model experiment and does not alter its settings.

For the desktop editor, open the `paper/` directory and select `manuscript/main.tex` as the main document. The project root must include the parent bibliography and evidence files. Desktop compilation succeeded with that root. Opening only the nested `manuscript/` directory prevents the editor from reading parent evidence paths.

The original ten-page publisher appendix remains unchanged. `build_dataset_evidence.py` can regenerate the additional dataset evidence PDF from the saved native browser screenshot; it does not recreate or impersonate the publisher webpage. Rebuilding that PDF requires rebuilding the manuscript to update its input hashes. `verify_manuscript.py` checks all eleven citation occurrences against bibliography numbers, evidence labels, source hashes, actual results-table rows, and the compiled page count. It also rejects unresolved references and overfull text boxes when local build logs are available.
