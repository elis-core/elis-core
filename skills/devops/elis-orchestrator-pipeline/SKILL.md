---
name: elis-orchestrator-pipeline
description: Orchestrator pipeline patterns — one active path, dependency hygiene
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-orchestrator-pipeline
    version: 1.0.0
    local_adapter: elis-research
    do_not_edit_directly: true
---

# ELIS Orchestrator Pipeline

## Purpose

Orchestrator pipeline patterns enforcing one active path per governed chain and strict dependency hygiene. Every governed workflow chain has exactly one active execution path at any time. Orphaned children of stale paths must be identified and archived before a new path is promoted. Dependency edges must be explicit and transitive — no implicit fan-in from unlinked tasks.

## Activation Conditions

This skill activates when any orchestrator agent (PM, Advisor, GitHub) is:
- Decomposing a governed workflow into child tasks
- Promoting a pipeline stage (e.g., from implementation to validation)
- Linking tasks with dependency edges
- Reconciling pipeline state before production activation

## Required Checks

- **Single active path:** Verify exactly one active execution path exists per governed chain
- **Orphan detection:** Identify children of stale/archived paths that must be unlinked or archived
- **Dependency graph:** Verify the full dependency graph is acyclic
- **Parent terminality:** Confirm all parent tasks are terminal (done/blocked) before promoting children
- **Explicit edges:** Verify no implicit fan-in — every dependency edge must be explicit
- **Stale path reconciliation:** Archive superseded paths and unlink stale dependencies before promoting new paths

## Outputs

- Pipeline state report listing all active paths and their children
- Stale path identification with recommended archive/unlink actions
- Dependency graph verification result (acyclic/cyclic)
- Promotion readiness assessment

## Blocking/Refusal Conditions

The orchestrator must refuse to proceed when:
- Multiple active paths exist for a single governed chain
- Orphaned children of stale paths are not reconciled before promotion
- Dependency graph contains cycles
- Not all parent tasks are terminal before child promotion
- Implicit fan-in edges are detected and not made explicit

## Pitfalls

- Kanban archive semantics: archiving a parent with linked children auto-archives children — unlink first
- promote --force bypasses dependency gates and should not be used in governed chains
- Stale descendants accumulate silently across pipeline iterations
- The PM does not execute repo operations — pipeline coordination and repo execution are separate roles

## References

- `_shared/architecture/` — ELIS governance pipeline documentation
- `~/.hermes/kanban/boards/elis-core/` — Live Kanban board for elis-core pipeline state