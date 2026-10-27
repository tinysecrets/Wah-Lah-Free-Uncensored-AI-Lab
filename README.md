# Wah-Lah Free Uncensored AI Lab

Wah-Lah Galaxy is the desktop interface for the local DAI router, voice, web search, workspace files, and coding tools.

## Current configuration

- Model route: `dai/auto` through `http://127.0.0.1:11435/v1`.
- Routing: the local DAI router manages selection and uses its hard-zero-cost, free-first configuration; paid routes remain disabled.
- Prompt: emphasizes direct, practical answers and tool use, without the old fixed Hermes/Septor requirement or the old blanket instruction to avoid system administration and coding topics.
- Voice: the existing G8 microphone and local speech output remain available.
- Tools: workspace-scoped file tools and operator-approved, isolated CLI checks remain enabled.
- Prompt logging remains disabled by default.

## Run and check

From this directory:

```bash
./launch.sh
./launch.sh --check
./launch.sh --list-models
```

The local router was verified on October 27, 2026. A direct chat request using `dai/auto` returned HTTP 200 and `READY`; that request reported `poolside/laguna-s-2.1:free` as its upstream model.

The app requests `dai/auto` and lets the local router select an available free model. The prompt can encourage direct answers, but upstream model/provider behavior is determined by the model selected by the router.
