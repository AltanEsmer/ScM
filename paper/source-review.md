# Source review for the prompt-format paper

Reviewed 23 October 2026. This is a focused review for the course-paper argument, not a systematic literature review. The ten sources below are published conference papers. Metadata was checked against official proceedings pages and the downloaded publisher PDFs in `work/paper-sources/`. Abstracts, relevant definitions, and available limitations sections were inspected. PDF page numbers below are one-based file pages. The publisher abstract on page 1 provides a compact evidence location for each proposed citation; the screenshot appendix must show the exact passage used for the final claim.

The proposed citations support background and measurement choices. None tests this study's requested model, twelve selected TACO tasks, three renderers, or execution endpoint. Differences among perturbations and outcomes prevent pooling their effects or treating them as predictions of this study's effect size.

## S01 — Formatting as a meaning-preserving intervention

Melanie Sclar, Yejin Choi, Yulia Tsvetkov, and Alane Suhr. 2024. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*. ICLR 2024.

[Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6c0e99d736da621403018ca7b32b1a4d-Abstract-Conference.html) · [Publisher PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/6c0e99d736da621403018ca7b32b1a4d-Paper-Conference.pdf)

Supported claim: meaning-preserving formatting choices produced substantial accuracy variation in the authors' few-shot evaluations of open models. Their FormatSpread method reports performance across sampled plausible formats. Evidence: abstract, PDF p. 1. Avoid presenting the largest reported spread as a typical effect or a prediction for code generation.

Critical boundary: Appendix C, PDF p. 29, notes that grammar-generated formats can be unusual and that evaluated tasks have relatively short instructions and input fields. This is the closest intervention match, but the tasks, models, few-shot setting, and format grammar differ from this study. Use it to justify measuring format effects, not to assert that the present formats must differ.

## S02 — Demonstration order is a different intervention

Yao Lu, Max Bartolo, Alastair Moore, Sebastian Riedel, and Pontus Stenetorp. 2022. *Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity*. ACL 2022, Volume 1: Long Papers, pp. 8086–8098.

[Proceedings and PDF](https://aclanthology.org/2022.acl-long.556/)

Supported claim: the order of a fixed set of few-shot demonstrations can materially change text-classification accuracy, and good permutations need not transfer across models. Evidence: abstract and Figure 1, PDF p. 1. The paper proposes entropy-based selection using an artificial development set across eleven classification tasks.

Critical boundary: this changes demonstration order, whereas the present renderers preserve canonical block order and add no demonstrations. Classification and older GPT-family models do not establish a code-format effect. Use this source to distinguish prompt intervention types and motivate explicit order control.

## S03 — The evaluator can change apparent sensitivity

Andong Hua, Kenan Tang, Chenhe Gu, Jindong Gu, Eric Wong, and Yao Qin. 2025. *Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs*. EMNLP 2025, pp. 19889–19899.

[Proceedings and PDF](https://aclanthology.org/2025.emnlp-main.1006/)

Supported claim: across seven models, six benchmarks, and twelve templates, replacing heuristic scoring with an LLM judge reduced measured performance variation and improved ranking consistency. Evidence: abstract, PDF p. 1.

Critical boundary: this supports evaluator dependence, not a conclusion that all sensitivity is artificial. The limitations section, PDF p. 6, acknowledges the twelve-template budget. An LLM judge is itself a measurement choice. This study instead executes code and compares output tokens against a fixed contract. Execution avoids judging semantic paraphrases of natural-language answers, but finite fixtures and extraction rules still bound what correctness means.

## S04 — Sensitivity varies across models, data, and instances

Jingming Zhuo, Songyang Zhang, Xinyu Fang, Haodong Duan, Dahua Lin, and Kai Chen. 2024. *ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs*. Findings of ACL: EMNLP 2024, pp. 1950–1976.

[Proceedings and PDF](https://aclanthology.org/2024.findings-emnlp.108/)

Supported claim: ProSA evaluates instance-level prompt sensitivity and reports variation across datasets and models. Evidence: abstract, PDF p. 1. Its PromptSensiScore and confidence analysis address a broader object than a single aggregate accuracy difference.

Critical boundary: model-size and confidence associations are empirical findings within its evaluated settings, not universal scaling laws. The few-shot discussion, PDF p. 5, notes computational limits on studying many exemplars. The course study neither implements PromptSensiScore nor observes token confidence. Task-level reporting here preserves heterogeneity without claiming to reproduce ProSA.

## S05 — Response likelihood is distinct from functional correctness

Anwoy Chatterjee, H S V N S Kowndinya Renduchintala, Sumit Bhatia, and Tanmoy Chakraborty. 2024. *POSIX: A Prompt Sensitivity Index For Large Language Models*. Findings of ACL: EMNLP 2024, pp. 14550–14565.

[Proceedings and PDF](https://aclanthology.org/2024.findings-emnlp.852/)

Supported claim: POSIX measures changes in the log-likelihood of a response under intent-preserving prompt variants. Evidence: abstract, PDF p. 1. Its reported associations with task type illustrate that a sensitivity result depends on both perturbation and outcome.

Critical boundary: likelihood sensitivity can exist even when two generated programs both pass all cases. The limitations section, PDF p. 9, reports quadratic comparisons in variants per prompt. POSIX is not computed here and the isolated interface does not expose the required likelihoods. Do not relabel zero pass-rate contrasts as zero POSIX sensitivity.

## S06 — Mitigation evidence has a task-specific scope

Yao Qiang, Subhrangshu Nandi, Ninareh Mehrabi, Greg Ver Steeg, Anoop Kumar, Anna Rumshisky, and Aram Galstyan. 2024. *Prompt Perturbation Consistency Learning for Robust Language Models*. Findings of ACL: EACL 2024, pp. 1357–1370.

[Proceedings and PDF](https://aclanthology.org/2024.findings-eacl.91/)

Supported claim: the authors evaluate synonym, oronym, and paraphrase perturbations in intent classification and slot filling, then train with a consistency objective to recover part of the performance loss. Evidence: abstract, PDF p. 1.

Critical boundary: the limitations section, PDF p. 9, explicitly says robustness improvements were evaluated on IC-SF tasks and may differ on real-world distributions. This is training-based mitigation, not a comparison of prose, list, and XML renderers. Mention only to delimit related robustness work; no mitigation is evaluated in this project.

## S07 — A sensitivity proxy need not be a pass-rate outcome

Sheng Lu, Hendrik Schuff, and Iryna Gurevych. 2024. *How are Prompts Different in Terms of Sensitivity?* NAACL 2024, Volume 1: Long Papers, pp. 5833–5856.

[Proceedings and PDF](https://aclanthology.org/2024.naacl-long.325/)

Supported claim: the authors find a negative association between their sensitivity estimate and accuracy, and propose sensitivity-aware decoding. Evidence: abstract, PDF p. 1. Their analysis concerns sensitivity of predictions to input perturbations under prompts.

Critical boundary: this operational definition differs from differences between renderer-level all-case success rates. The limitations section, PDF p. 9, restricts measurement mainly to close-ended generation and notes inference cost and closed-model reproducibility limits. Do not infer that the current ceiling implies low sensitivity under their estimator.

## S08 — Calibration addresses answer bias in few-shot prediction

Zihao Zhao, Eric Wallace, Shi Feng, Dan Klein, and Sameer Singh. 2021. *Calibrate Before Use: Improving Few-shot Performance of Language Models*. ICML 2021, PMLR 139, pp. 12697–12706.

[Official proceedings and PDF](https://proceedings.mlr.press/v139/zhao21c.html)

Supported claim: few-shot accuracy varied with prompt format, examples, and example order; contextual calibration reduced this instability in evaluated GPT-2 and GPT-3 settings. Evidence: abstract, PDF p. 1.

Critical boundary: calibration estimates answer bias using content-free inputs. It is not a general correction for arbitrary code generation and is not used here. Preserve the distinction between this published method and this repository's earlier phases called calibration.

Metadata discrepancy: the official PMLR page and BibTeX name the first author **Zihao Zhao**; the publisher PDF prints **Tony Z. Zhao**. These identify the same proceedings record. Use the proceedings BibTeX name consistently, and preserve the PDF's printed identity in screenshot evidence.

## S09 — Worst-case paraphrases answer a broader robustness question

Bowen Cao, Deng Cai, Zhisong Zhang, Yuexian Zou, and Wai Lam. 2024. *On the Worst Prompt Performance of Large Language Models*. Advances in Neural Information Processing Systems 37.

[Official proceedings and PDF](https://proceedings.neurips.cc/paper_files/paper/2024/hash/7fa5a377b7ffabcce43cd00231bb3f9c-Abstract-Conference.html)

Supported claim: RobustAlpacaEval evaluates semantically equivalent case-level queries and reports substantial best-to-worst variation among tested models. Evidence: abstract, PDF p. 1.

Critical boundary: its worst-prompt performance concerns a constructed set of paraphrases, not a lower bound over every possible prompt. The conclusion, PDF p. 10, acknowledges model coverage and alternative search methods as limits. The present three fixed renderers do not estimate adversarial or worst-case robustness. A three-format ceiling cannot contradict this study.

## S10 — Latent adversarial training is another mitigation approach

Tingchen Fu and Fazl Barez. 2025. *Same Question, Different Words: A Latent Adversarial Framework for Prompt Robustness*. EMNLP 2025, pp. 31305–31319.

[Proceedings and PDF](https://aclanthology.org/2025.emnlp-main.1595/)

Supported claim: the authors propose Latent Adversarial Paraphrasing, a training framework using continuous latent perturbations, and report improved worst-case win rates on their RobustAlpaca evaluation. Evidence: abstract, PDF p. 1.

Critical boundary: a latent continuous perturbation is not itself a human-readable prompt with proven semantic equivalence. The limitations section, PDF p. 9, restricts the study to text and mostly LoRA fine-tuning. Neither this training procedure nor a win-rate judge is used here. Avoid reproducing the abstract's ambiguous percentage wording when the outline only needs the qualitative mitigation claim.

## Synthesis for the course paper

Formatting is the direct motivation. Demonstration order, lexical perturbations, latent training, and adversarial paraphrases supply related context with different estimands. Likelihood changes, accuracy variation, judged win rates, and executable all-case success are different outcomes. The present contribution is a frozen, auditable comparison of three renderers in one bounded code-generation setting. Its observed ceiling is compatible with sensitivity under other outcomes, tasks, models, or perturbations.

All ten papers meet the requested published-conference source criterion. The review does not establish that they are the ten most relevant papers or exhaust the field. Final prose must cite only claims visible in its linked publisher evidence, and each citation occurrence needs its own appendix mapping.
