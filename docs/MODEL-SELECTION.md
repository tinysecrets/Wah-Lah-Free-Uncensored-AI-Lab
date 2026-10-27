# Model routing

Wah-Lah Free Uncensored AI Lab sends requests to the local DAI router at `http://127.0.0.1:11435/v1` using `dai/auto`.

The local router manages model selection and uses its hard-zero-cost, free-first configuration. Paid provider routes remain disabled. The app no longer pins inference to a single Hermes 3 / Septor upstream route or requires the returned upstream model name to match the router alias.

## Assistant prompt

The project prompt emphasizes direct, practical answers, useful tool calls, minimal boilerplate, and honest reporting when a tool fails. It removes the old blanket instruction to avoid shell, service management, and broader system work from the assistant's conversation style.

The prompt cannot override constraints imposed by a specific upstream model or inference provider. The router may choose different free models depending on availability.

## Execution permissions

The desktop app retains workspace-scoped file tools and operator-approved, isolated CLI checks. Those execution permissions are separate from the assistant prompt and model routing. Prompt logging remains disabled by default.
