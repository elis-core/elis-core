# PE closeout evidence — sandboxed elis-pm Kanban/A2A bridge

Date: 2026-07-06
Scope: sandboxed elis-pm production-readiness validation for authoritative Kanban and A2A diagnostic operation.

## Verdict

Runtime validation: PASS for controlled Kanban and A2A canary paths.

This is not blanket approval for unconstrained production dispatch. It validates the minimum safe runtime paths required before assigning controlled PM coordination work to sandboxed elis-pm.

## Validated architecture

sandboxed elis-pm -> NemoClaw/OpenShell governed REST policy -> 172.19.0.1:9510 host bridge -> sanctioned host Hermes Kanban CLI/API and official A2A SDK -> authoritative elis-core Kanban board and localhost A2A services.

## Safety rules

- No direct SQLite/database writes.
- Kanban mutation only through sanctioned Hermes Kanban CLI/API.
- A2A delivery only through official A2A SDK / localhost JSON-RPC /a2a.
- Sandboxed-local Kanban is not authoritative.
- nemoclaw exec payloads must be single-line command arguments.

## Kanban evidence

- Board: elis-core
- Task: t_beaf6284
- Title: KANBAN_A2A_SANDBOX_PM_CANARY_DO_NOT_USE
- Assignee: elis-pm
- Initial status: blocked
- Final status: done
- Run: #84, completed
- Mutation path: host bridge -> hermes kanban --board elis-core
- Direct DB write: false

Acceptance: CLOSE_OK=True; STATUS_AFTER=done; no direct DB write patterns in bridge.

## A2A evidence

- Direct PM client canary v2b: PM -> Advisor and PM -> Supervisor both completed.
- Host-side bridge A2A canary v3: OK=True, OPERATION=a2a_canary_send, TARGET=both.
- Final sandbox-origin A2A canary: HTTP_STATUS=200, OK=True, OPERATION=a2a_canary_send, TARGET=both.
- PM -> Advisor: TASK_STATE_COMPLETED.
- PM -> Supervisor: TASK_STATE_COMPLETED.
- Direct DB write: false.
- Direct Kanban mutation: false.
- Production dispatch: false.

Bridge log evidence: 172.19.0.2 POST /a2a/canary-send HTTP/1.1 200.

A2A service evidence: Advisor and Supervisor served /.well-known/agent-card.json and POST /a2a with HTTP 200.

## Active sandbox policies

- elis-kanban-a2a-bridge-readonly-ip
- elis-kanban-a2a-bridge-kanban-canary-write
- elis-kanban-a2a-bridge-a2a-canary-send

## Repo changes to review

- elis/a2a/pm/client.py: fixes protobuf Message construction.
- ops/kanban-a2a-bridge/bridge.py: captures current host bridge runtime implementation.
- ops/kanban-a2a-bridge/a2a_canary_send.py: captures standalone A2A canary helper.
- docs/hermes-migration/closeouts/pe-ops-sandboxed-pm-kanban-a2a-bridge-2026-07-06.md: this closeout evidence.

## Recommended next gate

Review scoped diff, then ask Advisor to validate the closeout evidence and repo diff before assigning controlled production PM coordination work to sandboxed elis-pm.
