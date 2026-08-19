---
name: elis-workspace-surface-audit
description: Live surface audit before tool or rule assumptions
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-workspace-surface-audit
    version: 1.0.0
    local_adapter: elis-research
    do_not_edit_directly: true
---

# ELIS Workspace Surface Audit

## Purpose

Live surface audit before any tool or rule assumptions are made. Before an ELIS agent invokes tools, applies governance rules, or makes decisions based on assumed workspace state, it must perform a live surface audit: verify what is actually on disk, in the board, in the repo, and in the running configuration. Assumptions derived from prior sessions, cached state, or static documentation must be validated against the live surface.

## Activation Conditions

This skill activates before any ELIS agent:
- Invokes filesystem tools based on assumed paths or content
- Applies governance rules that depend on current board state
- Makes decisions based on workspace topology from prior sessions
- References static documentation that may be stale

## Required Checks

- **Disk surface:** Verify actual filesystem state at target paths before reads or writes
- **Board surface:** Verify live Kanban board state (task status, parent/child relationships) before acting on assumptions
- **Repo surface:** Verify current git ref, branch, and remote state before repo operations
- **Config surface:** Verify running Hermes configuration, gateway status, and profile settings before config-dependent actions
- **Discrepancy report:** Document any mismatch between assumed and actual state before proceeding

## Outputs

- Live-surface verification results for each checked domain
- Discrepancy log when assumptions diverge from actual state
- Updated assumptions based on verified live surface

## Blocking/Refusal Conditions

The agent must refuse to proceed when:
- Assumed paths do not exist on disk and no fallback is authorised
- Board state contradicts assumed task statuses or dependency edges
- Repo is in a detached or unexpected state
- Running configuration does not match expected profile settings
- Discrepancies are detected and no PO approval exists to proceed despite them

## Pitfalls

- Cached session context from prior runs may reference stale paths or task IDs
- Static documentation (AGENTS.md, topology docs) may lag live state
- Gateway restart can change PID and service state without notice
- Board cleanup operations can alter dependency edges silently

## References

- `_shared/architecture/` — ELIS governance architecture documents
- `~/.hermes/config.yaml` — Running Hermes configuration
- `~/.hermes/kanban/boards/` — Live Kanban board databases