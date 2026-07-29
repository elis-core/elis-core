---
name: elis-tool-boundary
description: Strict tool-boundary rules for all ELIS agents
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-tool-boundary
    version: 1.0.0
    local_adapter: elis-slr
    do_not_edit_directly: true
---

# ELIS Tool Boundary

## Purpose

Strict tool-boundary rules for all ELIS agents. ELIS agents operate under strict tool-boundary constraints defined by their Hermes profile configuration. No agent may use tools outside its authorised toolset. Cross-profile tool access is prohibited unless explicitly authorised by PO. Platform tools code must never be modified by any ELIS agent.

## Activation Conditions

This skill is continuously active for all ELIS agents. It activates whenever an agent:
- Invokes a tool during any session
- Considers cross-profile operations (writing to another profile's files)
- Receives a task that may require tools outside its authorised toolset

## Required Checks

- **Toolset compliance:** Every tool invocation must be within the agent's authorised toolset as defined by its Hermes profile
- **Cross-profile guard:** Cross-profile writes require explicit PO direction and `cross_profile=True`
- **Platform code integrity:** No modification of platform tools code (Hermes agent code, gateway code, dispatcher code, tool implementations)
- **Tool-use audit trail:** Tool invocations must be traceable to authorised task scope

## Outputs

- Tool-boundary compliance self-assessment (for Advisor validation of tool-use)
- Violation report when boundary is approached or exceeded

## Blocking/Refusal Conditions

The agent must refuse when:
- A tool invocation is outside its authorised toolset
- A cross-profile operation is attempted without explicit PO authorisation
- A task requires platform tools code modification
- Tool-use scope exceeds the authorised task boundary
- A tool-boundary violation is detected — triggers immediate governance review

## Pitfalls

- Cross-profile soft guard fires even on `_shared/` writes — `_shared/` is a shared governance space but the guard treats it as cross-profile
- Terminal tool can bypass the guard but should not — use proper `cross_profile=True` parameter
- Tool-boundary violations by any ELIS agent are governance events, not technical errors
- Profile-level toolset configuration is the enforcement mechanism — governance rules supplement, not replace

## References

- `_shared/architecture/` — Agent authority boundary definitions
- `~/.hermes/profiles/<profile>/AGENTS.md` — Per-profile authority boundaries
- `_shared/SECURITY.md` — Security baseline including tool-use constraints