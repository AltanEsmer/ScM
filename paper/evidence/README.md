# Publisher screenshot index

These ten citation occurrences are planned in the current [outline](../outline.md). Each image is the publisher PDF page rendered with the exact claim passages highlighted. Provisional reference numbers follow first citation appearance in that outline. Reconcile them when the manuscript is drafted. See the [combined appendix](../output/citation-appendix.pdf).

| Occurrence | Provisional reference | Source and highlighted page | Supported outline claim |
| --- | --- | --- | --- |
| C01 | [1] | [S01, PDF p. 1](C01-S01-p1-highlight.png) | Formatting choices produced accuracy variation in the reported few-shot setting. |
| C02 | [2] | [S02, PDF p. 1](C02-S02-p1-highlight.png) | Changing demonstration order changed performance in the evaluated few-shot setting. |
| C03 | [4] | [S03, PDF p. 1](C03-S03-p1-highlight.png) | Heuristic scoring contributed to measured prompt sensitivity in the evaluated benchmarks. |
| C04 | [5] | [S04, PDF p. 1](C04-S04-p1-highlight.png) | ProSA studies instance-level prompt variation and reports variation across models and datasets. |
| C05 | [6] | [S05, PDF p. 1](C05-S05-p1-highlight.png) | POSIX measures response likelihood changes under prompt variation, a different endpoint from program correctness. |
| C06 | [8] | [S06, PDF p. 1](C06-S06-p1-highlight.png) | The authors study perturbations in intent classification and slot filling and propose consistency learning. |
| C07 | [7] | [S07, PDF p. 1](C07-S07-p1-highlight.png) | The authors use sensitivity as a performance proxy in their evaluated setting. |
| C08 | [3] | [S08, PDF p. 1](C08-S08-p1-highlight.png) | The authors report few-shot prompt instability and reduce variance using contextual calibration. |
| C09 | [9] | [S09, PDF p. 1](C09-S09-p1-highlight.png) | RobustAlpacaEval studies semantically equivalent case-level queries, a different intervention from fixed formats. |
| C10 | [10] | [S10, PDF p. 1](C10-S10-p1-highlight.png) | Latent Adversarial Paraphrasing optimizes trainable latent perturbations and model performance. |

The machine-readable [source manifest](sources.json) records publisher URLs, one-based PDF page indices, printed pagination, exact highlight excerpts, source hashes, and access date. The [render manifest](render-manifest.json) binds the PNGs and combined PDF to checksums and highlight coordinates.

Printed pagination differs by series. ACL screenshots show proceedings page numbers. The ICML first page does not print its proceedings page number, so its record gives the proceedings start page and says so. ICLR and NeurIPS conference PDFs use internal page 1, while their publisher BibTeX gives proceedings ranges 25055 to 25083 and 69022 to 69042, respectively. Use the visible publisher-PDF locator consistently.

Background source discussion is in the [source review](../source-review.md). These screenshots support the bounded claims listed here. They do not license broader claims about our model, code-generation tasks, or all prompt interventions.
