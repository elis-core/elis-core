---
name: HOST_KANBAN_A2A_BRIDGE_READONLY_SKILL
description: Read-only bridge access from sandboxed ELIS PM to the authoritative host ELIS Core Kanban board and host A2A service status.
---

# HOST_KANBAN_A2A_BRIDGE_READONLY_SKILL

## Purpose

Sandboxed ELIS PM must not treat sandbox-local Kanban state as authoritative.

The authoritative ELIS Core Kanban board runs on the original host Hermes instance. Sandboxed ELIS PM may verify board identity and A2A liveness only through the governed read-only host bridge.

## Canonical bridge

- URL base: `http://172.19.0.1:9510`
- Mode: read-only
- Network policy: `elis-kanban-a2a-bridge-readonly-ip`
- Allowed sandbox destination: `172.19.0.1:9510`
- Allowed methods: `GET` only

## Allowed endpoints

- `GET /health`
- `GET /kanban/identity`
- `GET /kanban/status-counts`
- `GET /a2a/status`

## Rules

1. The authoritative board is **only `elis-core`**. Do not use any other board as authoritative.
2. The authoritative path is through the host bridge via `hermes kanban --board elis-core`. Do not use sandbox-local Kanban CLI or database as the authoritative board.
3. Do not copy or mount the host Kanban database into the sandbox.
4. Do not use this read-only bridge for task mutation.
5. Treat A2A status from this bridge as liveness only, not as proof of message delivery.
6. Before assigning real PM tasks, run a controlled Kanban/A2A canary approved by PO.
7. PM must never write directly to any Kanban database.

## Validated evidence

- Host bridge service: `elis-kanban-a2a-bridge.service`
- Bridge bind: `172.19.0.1:9510`
- Board: `elis-core`
- Sandbox source observed by bridge: `172.19.0.2`
- A2A liveness: host ports `9500`, `9501`, `9502`, `9503` listening
