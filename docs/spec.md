# Prompt sensitivity pilot acceptance contract

Build a reproducible research pilot for three Python tasks, three introductory prompt variants, and five independent repetitions. Preserve the existing task specifications and prompt texts. Use 45 fresh Codex sessions requesting gpt-6.1-sol with medium reasoning. Keep research inputs out of each candidate working directory. Do not resume a session or show candidates tests, reference solutions, other outputs, or this protocol.

Save each exact prompt and raw answer with provenance, hashes, session identifier, timestamps, available usage, requested model and reasoning, observed tool events, and CLI version. Distinguish requested settings from provider-confirmed metadata. Preserve first attempts and failures. Resume without overwriting evidence or silently replacing unsuccessful generations.

Run generated code only in resource-limited Docker containers with networking disabled and without host credentials or personal directories. Determine results from trusted tests; generated stdout must never manufacture a passing verdict. Missing runs, execution failures, infrastructure failures, and protocol deviations must remain distinguishable. Report per-task, per-variant counts and limits of inference. Do not describe all-pass pilot results as proof that wording never matters.

Provide a usable CLI, behavioral tests, reproducible report, methodology, AI disclosure, and acceptance evidence. Review independently before publication. Use coherent Conventional Commits. Create a public GitHub repository if no relevant one exists and connect this folder. Preserve existing lecture PDFs and topic text locally and keep them out of Git, along with credentials and private logs.

The project contains pilot tooling and observations, not the final course paper or verified literature review.
