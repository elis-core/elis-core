# elis-pm Environment Requirements

This file documents required environment keys for the sandboxed `elis-pm` runtime.

Do not commit `.env`, raw tokens, API keys, bearer-style tokens, bot tokens, passwords, or credentials.

## Required for Hermes API server

These are generated/managed per sandbox:

```text
API_SERVER_PORT
API_SERVER_HOST
API_SERVER_KEY
```

## Required for Discord operation

These must be supplied through the approved credential mechanism, not committed to Git:

```text
DISCORD_BOT_TOKEN
DISCORD_ALLOWED_USERS
DISCORD_HOME_CHANNEL
DISCORD_ALLOWED_CHANNELS
DISCORD_REQUIRE_MENTION
DISCORD_FREE_RESPONSE_CHANNELS
DISCORD_ALLOW_BOTS
DISCORD_APPLICATION_ID, where used
```

## Provider/model credentials

Provider credentials must be supplied through the approved credential mechanism, not committed to Git:

```text
OPENROUTER_API_KEY
ANTHROPIC_TOKEN
ANTHROPIC_API_KEY
ZENMUX_API_KEY
OPENCODE_ZEN_API_KEY
```

## Do not migrate blindly

Do not copy these from the current non-sandboxed profile into the sandbox or repo as configuration:

```text
.env
.env.bak*
config.yaml.bak*
```

## Runtime configuration boundary

`config.yaml` is runtime-generated for sandboxed ELIS agents and must not be copied from a host or stale repo profile into an active sandbox.

The active sandbox provider route is managed by the sandbox runtime and may include managed-provider settings such as `nvidia-prod` via `https://inference.local/v1`.

The repo may contain `config.runtime.template.yaml` as a sanitized reference template. It is not an active runtime config and must not contain real credentials.

Before any future sandbox copy operation, verify that active runtime model/provider access remains valid and that `config.yaml` was not replaced by a stale host profile copy.

## Host Kanban/A2A read-only bridge

The authoritative ELIS Core Kanban board remains on the original host Hermes instance.

The authoritative board is **only `elis-core`**. The authoritative path is through the host bridge via `hermes kanban --board elis-core`.

Sandboxed ELIS PM accesses host Kanban/A2A status through the governed read-only bridge:

- Base URL: `http://172.19.0.1:9510`
- Sandbox policy preset: `elis-kanban-a2a-bridge-readonly-ip`
- Mode: read-only
- Allowed operations: `/health`, `/kanban/identity`, `/kanban/status-counts`, `/a2a/status`

Sandbox-local Kanban files are not authoritative. PM must never write directly to any Kanban database. Real task assignment requires a separate controlled canary validating Kanban write and A2A message delivery.
