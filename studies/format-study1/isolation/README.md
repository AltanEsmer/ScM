# Isolated generation preparation

Run from any directory:

```sh
python3 studies/format-study1/isolation/run.py offline-proof --evidence /tmp/isolation-proof.json
```

This builds Codex CLI 0.157.1 and exercises its real app-server against a local,
non-forwarding Responses fixture. It makes **zero inference-provider requests**
and produces **zero candidate trials**. Building downloads public npm packages.
The returned literal `OFFLINE_OK` is synthetic protocol data, not a model answer.

The generation container has no host mounts, repository, reference, test, previous
answer, credential, or Docker socket. Its root is read-only, its only writable
filesystem is temporary, and it runs as UID 65534 with no Linux capabilities.
An internal Docker network prevents direct public egress. Only the fixture relay
is reachable. Host filesystem canaries remain outside all mounts, and runtime
checks inspect protected paths and test direct public/host-gateway connectivity.
The host and Docker daemon remain trusted; this does not defend against a daemon
administrator or kernel vulnerability.

The client uses a fresh temporary CODEX_HOME and HOME; no host configuration,
history, auth, or skills are copied. `thread/start` and `turn/start` use empty
environments, `allowProviderModelFallback=false`, exact requested model
`gpt-6.1-sol`, and `medium` effort. No project instructions are loaded. The relay
fails closed on wrong inference paths, model, effort, tool-output/history inputs,
or any tools. The real-client offline capture confirmed an empty tool list;
actual tool declarations are retained in evidence. Every proof and future launch also
hashes the three runtime modules inside the selected image and compares them with
the reviewed host files, including when an existing image is reused. It never opens
an outbound connection, so an accidental client request cannot reach a provider.

## Evidence and live gate

Successful offline proof status is
`offline_isolation_verified_live_preflight_pending`, **not ready for collection**.
The future live code exists but neither live entrypoint has been executed.
Without `--authorize-live`, both commands exit before reading authentication or
sending a request. These commands are instructions for a future authorized run:

```sh
python3 studies/format-study1/isolation/run.py live-preflight --authorize-live --evidence /private/run/live-canary.json
python3 studies/format-study1/isolation/run.py generate --authorize-live --canary /private/run/live-canary.json --trial-id FROZEN_TRIAL_ID
```

Do not run either command as part of preparation. Each authorized invocation can
send one inference request. Both require the full frozen manifest and matching
offline proof, source hashes, and immutable image ID. `generate` also requires a
successful live canary for that same manifest/image/source and accepts only a
trial's exact frozen prompt path/hash. The candidate receives prompt text only.
Generation enforces the frozen schedule and creates runs/TRIAL_ID/dispatch.json
before authentication or dispatch. It writes result.json once. An existing or
ambiguous attempt cannot be retried; a failed/ambiguous prior attempt blocks the
schedule. No automatic transport retry can reach the provider: the live relay
accepts at most one upstream request per invocation.

The trusted relay reads file-backed ChatGPT login `tokens.access_token` and
`tokens.account_id` only when a future live command passes all gates. Credentials
travel through the relay's stdin into memory, never via candidate environment,
mounts, repository files, command arguments, or logs. The relay alone is attached
to an external Docker network. The candidate remains on the internal network.
The fixed destination is `https://chatgpt.com/backend-api/codex/responses`, using
Bearer authorization and `ChatGPT-Account-ID`, as documented in matching-version
source. It permits no alternate destination, path, redirects, tools, or models.
It passes provider SSE after validating completed-response identity; wrong or
missing identity fails closed. Reported identity is **not** independent model
attestation. Unavailable model, expired/rejected login, or unsupported provider
transport blocks collection. Refresh is deliberately unsupported; future login
must be renewed through the normal Codex login flow outside this experiment.

Live-canary success requires the synthetic marker `SCM_LIVE_CANARY_OK`. Its record
binds source hashes, image ID, freeze hash, requested model/effort, and reported
model. The current offline proof establishes no live provider compatibility.
Mock HTTPS/auth tests exercise the live transport without network or real auth:

```sh
node studies/format-study1/isolation/test_live_transport.mjs
python3 -m unittest discover -s studies/format-study1/isolation -p 'test_*.py' -v
```

## Supported-version evidence

- Installed `codex --version`: `codex-cli 0.157.1`.
- `codex app-server generate-json-schema --experimental --out DIR` documents
  `ThreadStartParams.environments`: empty disables environment access, and
  `allowProviderModelFallback` controls replacement of unavailable models.
- Official pinned source:
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/core/src/tools/spec_plan.rs
  gates shell (1041), patch (1216), and image (1230) on environment presence.
- Official config schema:
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/core/config.schema.json
  supports project_doc_max_bytes=0 and skills.include_instructions=false.
  It does not expose tools.disable_defaults. No unsupported no-tools flag is used.

- ChatGPT base URL (line 77):
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/model-provider-info/src/lib.rs
- Bearer and account headers (lines 31–43):
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/model-provider/src/bearer_auth_provider.rs
- POST `/responses` wire path (lines 138–141):
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/codex-api/src/endpoint/responses.rs

- Default originator and user-agent headers (lines 42 and 435–439):
  https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/login/src/auth/default_client.rs
