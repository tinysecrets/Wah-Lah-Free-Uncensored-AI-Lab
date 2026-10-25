# Fixed-model decision record — Galaxy Edition

## Single intended allowlist entry — currently unavailable at $0

Hermes 3 Llama 3.1 405B — intended ID: nousresearch/hermes-3-llama-3.1-405b:free

Nous Research describes Hermes 3 as uncensored and steerable. However, the live OpenRouter model lookup returned HTTP 404 for the exact :free variant during this setup. OpenRouter's current base-model entry is priced at $1 per million input tokens and $1 per million output tokens. The shared FreeLLMAPI row is also disabled / needsKey. The app's verification therefore fails and the Galaxy Send button remains disabled. This is intentional: the client must not use the paid base ID, auto routing, or a different model as a workaround.

Sources:
- Free-variant listing: https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b:free/pricing
- Current base pricing: https://openrouter.ai/nousresearch/hermes-3-llama-3.1-405b
- OpenRouter model lookup docs: https://openrouter.ai/docs/api/api-reference/models/get-model
- Publisher release: https://nousresearch.com/freedom-at-the-frontier-hermes-3

The base model is scheduled to go away on **November 2, 2026**, so a future replacement must be identified by exact model ID and separately verified as explicitly uncensored and $0 before it can be activated. No paid or alternate-model fallback is configured.

## Why not FreeLLMAPI inference right now?

The local FreeLLMAPI service at 100.105.171.108:3001 is healthy, but its /v1/models list reports Hermes 3 405B as available:false, unavailable_reason:"disabled", execution_status:"needsKey". Qwen3 235B, Qwen3.5 397B, Qwen3 Coder Plus, and the small explicitly uncensored Gemma rows are also disabled under the current provider setup. The shared service is not reconfigured. OpenRouter is used directly for this folder's exact :free model, not as an auto/fallback list.

## Qwen / Dolphin / abliterated candidates

- Qwen3-235B-A22B has 235B total parameters and 22B active, but a standard Qwen3 Instruct/Thinking build is not automatically uncensored.
- Qwen3.5 397B is present in the local FreeLLMAPI catalog, but is disabled there and not verified as an uncensored fine-tune.
- The old Dolphin3.0 Mistral 24B :free catalog page appears stale: the current OpenRouter model API showed a priced Venice Uncensored Dolphin-Mistral 24B entry, not an available $0 route. It is also much smaller than the requested size.
- An exact Qwen/Dolphin/abliterated fine-tune must be identified and its $0 route verified before it may enter the allowlist. No unverified model is added as a backup.

## Guardrails

The app uses the existing OpenRouter key stored owner-only. Its inference request uses the exact :free model ID. It checks model identity and pricing, restricts files to workspace, requires approval for edits/CLI execution, and exposes no general shell or service control. Existing D-A-I routing and FreeLLMAPI service configuration remain unchanged.
