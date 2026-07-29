---
name: elis-implementer-self-check
description: Mandatory implementer self-check before Advisor validation
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-implementer-self-check
    version: 1.0.0
    local_adapter: elis-slr
    do_not_edit_directly: true
---

# ELIS Implementer Self-Check

## Purpose

Mandatory implementer self-check before Advisor validation. Before submitting any artifact or packet for Advisor validation, the implementing agent must run a prescribed self-check checklist. This skill is binding on all implementing agents (elis-pm, elis-supervisor, elis-github).

## Activation Conditions

This skill activates whenever an implementing agent:
- Completes an implementation artifact (SKILL.md, gate packet, configuration)
- Prepares to submit work for Advisor validation
- Finishes a remediation pass before re-submission

## Required Checks

- **Forbidden-literal scan:** `grep -Fc` scan for deprecated names, forbidden terms, and stale references as specified in the task body
- **File-existence verification:** Confirm all expected output files exist at their target paths
- **Line-count confirmation:** Verify line counts match expected ranges from the task specification
- **Artifact-freeze integrity:** Verify SHA256 of frozen artifacts matches the expected hash; verify detached `.sha256` sidecar is present and valid
- **Constraint-compliance:** Verify all task-specified constraints are met (no prohibited operations, no scope creep)
- **Self-check manifest:** Each checklist item must produce an explicit PASS/FAIL result

## Outputs

- Self-check checklist with explicit PASS/FAIL per item
- Forbidden-literal scan results with matched counts
- File-existence and line-count verification
- SHA256 verification results for frozen artifacts
- Constraint-compliance report

## Blocking/Refusal Conditions

The implementer must refuse to submit for Advisor validation when:
- Any self-check item returns FAIL
- Forbidden literals are present in the artifact
- Expected output files are missing
- SHA256 verification fails for referenced artifacts
- Any task-specified constraint is violated

## Pitfalls

- Self-check is not a substitute for Advisor validation — it is a pre-filter
- A PASS on self-check does not guarantee Advisor PASS — the Advisor has independent criteria
- Self-check results must be included in the implementation manifest for auditability
- Skipping self-check and submitting directly to Advisor is a governance violation

## References

- `_shared/architecture/` — Validation governance rules
- `_shared/SECURITY.md` — Forbidden-literal and constraint reference