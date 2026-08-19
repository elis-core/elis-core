---
name: elis-skill-health
description: Skill-health feedback from recurring failures
version: 1.0.0
author: ELIS PM
platforms: [linux]
environments: [kanban, hermes]
metadata:
  hermes:
    tags: [elis, governance]
    shared_skill: true
    origin_repo: elis-core
    origin_skill: elis-skill-health
    version: 1.0.0
    local_adapter: elis-research
    do_not_edit_directly: true
---

# ELIS Skill Health

## Purpose

Skill-health feedback from recurring failures. When any governed skill produces repeated PARTIAL or FAIL findings across remediation loops, the skill itself must be amended rather than continuing to patch individual artifacts. This closes the loop between validation failures and skill improvement, preventing the same failure pattern from recurring across different implementation chains.

## Activation Conditions

This skill activates when:
- A governed skill produces repeated PARTIAL or FAIL findings across remediation loops (3 loops exhausted per elis-verification-loop)
- The same failure pattern appears across different implementation chains
- The Advisor identifies a systemic skill defect rather than an artifact-specific error
- The PO requests a skill-health review

## Required Checks

- **Pattern documentation:** Document the failure pattern — which skill, which findings, across which chains
- **Root cause:** Distinguish between artifact-specific error and systemic skill defect
- **Amendment scope:** Define what must change in the skill to prevent recurrence
- **Amendment validation:** Amended skill must be validated by Advisor against the original failure pattern
- **PO approval:** Amended skill requires PO approval before adoption

## Outputs

- Skill-health finding report documenting the failure pattern
- Skill-amendment task (created by PM) with amendment specification
- Validated amended skill (after Advisor validation)
- PO-approved amended skill ready for adoption

## Blocking/Refusal Conditions

The skill-health process must refuse when:
- Failure pattern has not been validated as systemic by the Advisor
- Amendment scope exceeds the PO-authorised change boundary
- Amended skill has not passed Advisor validation
- PO has not approved the amendment

## Pitfalls

- Skill-health amendment is not a fourth remediation loop — it is a separate governance process
- Amendments must target the skill, not individual artifacts
- Documenting the failure pattern is the Advisor's role; implementing the amendment is the PM's role
- Skills with `do_not_edit_directly: true` must be amended at the canonical source (elis-core), not at the SLR adapter copy

## References

- `elis-verification-loop` — Loop counting and exhaustion trigger
- `elis-implementer-self-check` — Self-check discipline that may surface systemic patterns
- `_shared/architecture/` — Skill governance and amendment authority