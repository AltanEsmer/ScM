# Design decision

Two independent reviewers proposed a flat file-based project and a typed package. An independent cross-review scored them against interface size, preserved first attempts, honest provenance, trustworthy scoring, and implementation cost. The file design scored 24 of 25 and the package scored 18 of 25. These are design judgments, not research measurements.

Choose the file design. The project needs immutable experiment inputs, per-trial records, a Docker grader, and derived reports. It does not need a database, hosted service, or automated API collection adapter. The coordinator collects through the native session tool because the CLI cannot use the requested model on this account.

Adopt the package proposal's strict nested type checks, explicit failure categories, and meaningful faulty-function fixtures. Keep a single owner for code and one coordinator for evidence and Git. Each trial owns its directory. Reports are regenerated from verified records.

The original pilot executed candidate code alongside its expected outputs. The new grader keeps expectations on the host and treats container output as untrusted observations. This change protects the scoring boundary against forged pass messages. It does not make a candidate-controlled Python interpreter a trusted source for values, types, mutation, or identity evidence against deliberate tampering.

The initial repository has no existing implementation branch or upstream history. Work stays on the current main branch as requested by the implement skill. Independent review compares the project against bootstrap commit de1a7d6. A separate pull request is unnecessary for this first repository publication. Later changes can use pull requests against this baseline.
