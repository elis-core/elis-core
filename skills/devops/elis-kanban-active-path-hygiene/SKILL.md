---
name: elis-kanban-active-path-hygiene
description: Stale descendant hygiene and active-path rules
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-kanban-active-path-hygiene
    version: 1.0.0
    local_adapter: elis-research
    do_not_edit_directly: true
---

# ELIS Kanban Active-Path Hygiene

## Purpose

Stale descendant hygiene and active-path rules. Before promoting any new active path, the orchestrator must identify and reconcile all stale descendants of prior paths. Stale children must be unlinked from their parent before the parent is archived, or the parent archive will auto-archive the children. This skill is invoked at gate-review time by the PM before repo sync or production activation.

## Activation Conditions

This skill activates when:
- A new active path is being promoted for a governed chain
- A gate-review is being performed before repo sync or production activation
- Board cleanup is required to reconcile pipeline state
- Stale dependency edges are detected

## Required Checks

- **Orphan identification:** Scan for children of archived/superseded paths that are still linked
- **Stale path detection:** Identify paths that have been superseded by newer pipeline iterations
- **Unlink verification:** Confirm stale dependencies are unlinked before parent archive
- **Single-path enforcement:** Verify exactly one active path remains per governed chain after reconciliation
- **Archive safety:** Verify that parent archive will not auto-archive unintended children

## Outputs

- Orphan and stale-path inventory
- Recommended unlink actions for each stale dependency
- Pre-archive safety assessment
- Post-reconciliation board state confirmation

## Blocking/Refusal Conditions

The orchestrator must refuse repo sync or production activation when:
- Stale descendants remain linked to parents marked for archive
- Multiple active paths exist for the same governed chain
- Orphans are identified but not yet reconciled
- Pre-archive safety check fails

## Pitfalls

- Archive with linked children silently cascades — archiving a parent with live children is destructive
- `promote --force` bypasses dependency gates — never use in governed chains
- Stale paths accumulate silently across pipeline iterations if not explicitly tracked
- Board state can change between audit and action — re-verify before executing archive/unlink

## References

- `elis-orchestrator-pipeline` — Pipeline patterns this hygiene skill supports
- `~/.hermes/kanban/boards/elis-core/` — Live Kanban board for hygiene operations