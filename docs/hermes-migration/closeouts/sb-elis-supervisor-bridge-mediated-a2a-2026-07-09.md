# sb elis-supervisor Bridge-Mediated A2A Closeout — 2026-07-09

## Scope

This closeout documents the sb elis-supervisor bridge-mediated A2A validation and least-privilege policy cleanup.

The implementation follows the clean bridge-mediated model:

- sandboxed agents access only the ELIS Kanban/A2A bridge;
- raw host A2A ports remain private localhost implementation details;
- bridge owns registry, route visibility, and canary mediation;
- no direct raw A2A port access is granted to sb elis-supervisor.

## Validated topology

Bridge:

    172.19.0.1:9510  ELIS Kanban/A2A bridge

Host-local A2A services, not sandbox-facing:

    127.0.0.1:9500  host elis-advisor
    127.0.0.1:9501  host elis-supervisor
    127.0.0.1:9502  host elis-pm
    127.0.0.1:9503  host elis-github

## sb elis-supervisor policy state

Applied custom policy:

    elis-sb-supervisor-bridge-only

Allowed sandbox-facing bridge endpoint:

    172.19.0.1:9510

Broad policies removed from sb elis-supervisor:

    brew
    huggingface
    npm
    weather

Preserved active policies/capabilities:

    discord
    pypi
    managed_inference / nvidia
    elis-sb-supervisor-bridge-only

## Bridge endpoints added / validated

The bridge now exposes:

    GET  /a2a/registry
    GET  /a2a/agents
    GET  /a2a/routes
    GET  /kanban/status
    POST /a2a/canary

/kanban/status is an alias for the existing /kanban/status-counts.

/a2a/canary is an alias for the existing /a2a/canary-send.

## Validation summary

Validated from sb elis-supervisor:

    /health          PASS
    /kanban/status   PASS
    /a2a/status      PASS
    /a2a/registry    PASS
    /a2a/agents      PASS
    /a2a/routes      PASS

Raw host A2A port negative test:

    172.19.0.1:9500  not reachable
    172.19.0.1:9501  not reachable
    172.19.0.1:9502  not reachable
    172.19.0.1:9503  not reachable

Bridge-mediated A2A canary:

    sb elis-supervisor -> 172.19.0.1:9510/a2a/canary
    bridge -> host-local A2A SDK -> 127.0.0.1:9501/a2a
    result: completed=true
    direct_db_write=false
    direct_kanban_mutation=false
    production_dispatch=false

## Registry authority model

The registry records:

- elis-pm as peer domain project manager for elis-core;
- elis-slr as peer domain project manager for elis-slr;
- sb elis-supervisor as candidate runtime for elis-supervisor;
- host elis-supervisor as current active/fallback runtime;
- specialist_slr_agent as SLR-domain specialist, not a project manager;
- raw host A2A ports as non-sandbox-facing.

## Intended repo files from this work

    ops/kanban-a2a-bridge/bridge.py
    ops/kanban-a2a-bridge/a2a_bridge_registry.json
    ops/kanban-a2a-bridge/sb-elis-supervisor-runtime-guardrail.md
    ops/nemoclaw/policies/elis-sb-supervisor-bridge-only.yaml
    docs/hermes-migration/closeouts/sb-elis-supervisor-bridge-mediated-a2a-2026-07-09.md

## Provenance caveat

ops/kanban-a2a-bridge/bridge.py currently contains mixed-provenance working-tree changes.

Pre-existing before today’s A2A patch:

    /kanban/create production endpoint
    ALLOWED_ASSIGNEES
    kanban_create_task()
    board fail-closed assertion

Added by today’s A2A bridge-mediated work:

    A2A_REGISTRY_PATH
    load_a2a_registry()
    a2a_registry()
    a2a_agents()
    a2a_routes()
    GET /a2a/registry
    GET /a2a/agents
    GET /a2a/routes
    GET alias /kanban/status
    POST alias /a2a/canary

Do not attribute the pre-existing /kanban/create changes to this A2A/sb supervisor closeout unless PO explicitly approves including them in the same commit.

## Commit recommendation

Preferred clean commit strategy:

1. either commit or separately reconcile the pre-existing /kanban/create bridge changes;
2. then commit the A2A bridge-mediated registry/policy/guardrail changes;
3. do not include unrelated untracked files shown by full repo status.

## Status

Result: PASS for bridge-mediated A2A validation and least-privilege sb elis-supervisor policy cleanup.

Discord cutover remains out of scope until PO explicitly approves a temporary cutover window.
