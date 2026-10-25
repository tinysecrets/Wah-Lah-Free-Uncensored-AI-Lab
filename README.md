# Wah-Lah Free Uncensored AI Lab — Galaxy Edition

A standalone desktop app with a strict single-model target, speech input/output, and guarded coding tools. The model is explicitly uncensored, but its proposed free API variant is currently returning 404, so inference stays locked until a valid $0 endpoint is verified. The app does not restart or reconfigure D-A-I or FreeLLMAPI.

## Selected model target — currently blocked at $0

- Hermes 3 Llama 3.1 405B
- Exact intended API ID: nousresearch/hermes-3-llama-3.1-405b:free
- Nous Research describes Hermes 3 as uncensored and steerable.
- **Live verification on October 25, 2026:** OpenRouter's public model lookup returned HTTP 404 for the :free variant. Its currently listed base model is priced at $1 per million input and output tokens. The existing FreeLLMAPI service also reports the 405B row disabled / needsKey.
- Therefore, chat is intentionally disabled until that exact :free variant becomes verifiable at $0. Do not remove the suffix, select :auto, or use another model to get around this. This is the deliberate no-spending/no-wrong-model safeguard.
- OpenRouter marks the base Hermes 3 405B model as going away November 2, 2026, so a replacement may eventually be necessary—but it must meet the same explicitly-uncensored and $0 criteria.

Sources:
- https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b:free/pricing
- https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b
- https://openrouter.ai/docs/api/api-reference/models/get-model
- https://nousresearch.com/freedom-at-the-frontier-hermes-3

## Why it uses OpenRouter directly

The existing FreeLLMAPI service is healthy at http://100.105.171.108:3001, but its model catalogue currently marks Hermes 3 405B disabled / needsKey. The big Qwen models and its explicitly uncensored small Gemma entries are also disabled under the current provider configuration. This app does not modify that shared service.

For this app only, inference is configured for one exact OpenRouter :free model ID using an existing local key. The live metadata request currently returns 404 for that variant, so the chat send button remains disabled; the app will not call the paid base model, FreeLLMAPI auto routing, or another model. FreeLLMAPI health is checked separately, never used as fallback. No key is printed.

## Launch

Double-click “Wah-Lah Free Uncensored AI Lab.desktop” on the Debian Desktop, or run ./launch.sh in this folder. It opens the Galaxy GUI.

- ./check-health.sh checks the shared FreeLLMAPI health endpoint and local settings without changing services.
- ./launch.sh --check verifies the exact model and $0 metadata through OpenRouter.
- ./launch.sh --setup-key prompts for the OpenRouter key using hidden terminal input.
- ./launch.sh --list-models lists model IDs visible to the key for research only; it does not add them to the allowlist.
- ./launch.sh --cli opens the alternate text interface.

## Keys and privacy

- .secrets/openrouter-api-key is the inference key, mode 0600; .secrets/ is mode 0700.
- .secrets/api-key is the separate local FreeLLMAPI client key; it is not sent to OpenRouter.
- Keys are never printed to the GUI or logs. Secret files, workspace contents, and logs are excluded by .gitignore.

## Voice

- Speech output uses local spd-say and is enabled by default.
- Press “Listen · G8 Mic · 8 sec” to record from the existing LG G8 source android-87f1610 and transcribe locally with Vosk small-en.
- The transcript appears in the message box for review; nothing is sent until you press Send.
- No new microphone daemon is installed and no other audio services are restarted.

## Guarded coding tools

- Public web search and arithmetic.
- Workspace-only file listing and reads.
- Every model-proposed file write requires GUI approval.
- CLI tools are restricted to directory listing, Python/Node syntax checks, pytest, Git status, and Git whitespace checks. Code-executing CLI actions require a separate approval and run inside bubblewrap: no network, no home directory, read-only OS filesystem, only workspace/ writable, and a 30-second timeout.
- No arbitrary shell, service control, package installation, global filesystem access, or credential-reading tool is exposed to the model.
- Prompts and completions are not written to logs by default.

## Qwen / Dolphin / abliterated note

Qwen3-235B-A22B is 235B total parameters with 22B active, but the standard Instruct/Thinking builds are not automatically uncensored. Dolphin is a separate fine-tune family. The older Dolphin3.0 Mistral 24B :free page appears stale: the current OpenRouter API returned a priced Venice Uncensored Dolphin-Mistral 24B listing, not a zero-price route. It is much smaller than the preferred frontier-scale option. An alternative Qwen/Dolphin/abliterated model will only be added after its exact build is verified as uncensored and a $0 endpoint is confirmed. It will not be a silent fallback.

## Folder map

- app/galaxy.py — Galaxy GUI.
- app/lab.py — model client and restricted tools.
- config/models.json — single exact model allowlist.
- config/settings.json — endpoint and safe defaults.
- .secrets/ — owner-only keys.
- workspace/ — only agent-controlled file workspace.
- assets/galaxy.svg — Galaxy icon.
- launch.sh and check-health.sh — launcher and preflight.
