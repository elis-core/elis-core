---
name: elis-verification-loop
description: Verification loop — implementer self-check, Advisor validation, PO approval
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-verification-loop
    version: 1.0.0
    local_adapter: elis-slr
    do_not_edit_directly: true
---

# ELIS Verification Loop

## Purpose

Verification loop before handoff. Every implementation artifact must pass through a verification loop before being handed off to the next stage. The loop consists of: (a) implementer self-check, (b) Advisor validation, (c) PO approval where required by governance. The verification loop is not a trial-and-error cycle — it is exception handling. Repeated PARTIAL or FAIL findings trigger skill-health amendment rather than further remediation loops.

## Activation Conditions

This skill activates when:
- An implementation artifact is being handed off between stages
- A validation verdict (PASS/PARTIAL/FAIL/BLOCKED) is returned
- A remediation loop is being initiated
- Maximum remediation loop count is approached or exceeded

## Required Checks

- **Stage ordering:** Verify all stages are completed in order — no skipped stages
- **Loop count:** Track remediation loop count; maximum three remediation loops per implementation task
- **Verdict routing:** PASS → complete; PARTIAL/FAIL/BLOCKED → block with reason
- **Skill-health trigger:** After third non-PASS verdict, trigger skill-health amendment (elis-skill-health) instead of further remediation
- **PO escalation:** When max loops exhausted, present PO with options A–F for decision

## Outputs

- Verification trail documenting each stage, verdict, and loop count
- Loop-exhaustion PO decision packet when applicable
- Skill-health trigger notification to PM for recurring failure patterns

## Blocking/Refusal Conditions

The verification loop must refuse when:
- Stages are skipped or executed out of order
- Self-check was not performed before Advisor validation
- Implementation artifact is submitted directly for PO approval bypassing Advisor validation
- Remediation loop count exceeds three without PO decision

## Pitfalls

- Validation verdicts are terminal — PARTIAL/FAIL/BLOCKED must use `kanban_block`, not `kanban_complete`
- `kanban_complete` with non-PASS verdict is a lifecycle violation regardless of task body enumeration
- Skill-health amendment is the mechanism for continuous improvement — do not create a fourth remediation loop
- The Advisor identifies findings; the implementer remedies them — roles do not cross

## References

- `elis-implementer-self-check` — Pre-Advisor self-check discipline
- `elis-skill-health` — Skill amendment process for recurring failures
- `_shared/architecture/` — Verification governance rules