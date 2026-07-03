# ELIS 2-Agent Principle v1.0

> **Metadata**  
> **Title:** ELIS 2-Agent Principle v1.0  
> **Repository:** elis-core  
> **Status:** Approved  
> **Version:** 1.0  
> **Last Updated:** 2026-07-03  
> **Owner:** ELIS PM  
> **Approver:** Carlos Rocha (PO)

## Purpose

The ELIS 2-Agent Principle is a core architectural rule for ELIS. Every
meaningful autonomous activity is executed by **two independent
agents**:

1.  **Implementation Agent** --- performs the assigned work.
2.  **Validation Agent** --- independently evaluates the work before it
    can progress.

This separates implementation from approval and reduces the risk of
shared blind spots.

## Adversarial Validation

The validator is intentionally independent.

It should, whenever practical:

-   Run in a different OpenShell sandbox.
-   Use a different OpenShell gateway.
-   Use a different foundation model.
-   Execute in a fresh session.
-   Reproduce or verify results from evidence rather than trusting the
    implementer.
-   Return PASS, FAIL, or BLOCKED with supporting evidence.

The validator is expected to challenge assumptions, detect errors, and
reject work that does not meet governance or technical requirements.

## Runtime Isolation

Each agent has:

-   Dedicated NemoHermes sandbox
-   Dedicated OpenShell gateway
-   Dedicated managed inference route
-   Dedicated filesystem
-   Minimal network policies

Agents communicate through A2A, Kanban state, and approved
artefacts---not shared filesystems.

## Standard Workflow

PM → Reset implementer session → Implementer → Reset validator session →
Validator → PM review → ELIS GitHub (when applicable) → PO approval
(when required)

## ELIS Core Agent Pairs

  -----------------------------------------------------------------------
  Activity                Implementer             Validator
  ----------------------- ----------------------- -----------------------
  Platform implementation elis-supervisor         elis-advisor

  GitHub publication      elis-github             elis-advisor

  A2A/runtime             elis-supervisor         elis-advisor
  implementation                                  

  PM coordination         elis-pm                 elis-advisor
                                                  (governance review as
                                                  required)
  -----------------------------------------------------------------------

## ELIS SLR Agent Pairs

  -----------------------------------------------------------------------------
  Activity                Implementer             Validator
  ----------------------- ----------------------- -----------------------------
  Literature harvesting   elis-slr-harvest        elis-slr-harvest-validator

  Study screening         elis-slr-screen         elis-slr-screen-validator

  Data extraction         elis-slr-extract        elis-slr-extract-validator

  Evidence synthesis      elis-slr-synth          elis-slr-synth-validator

  Protocol & methodology  elis-slr-protocol       elis-slr-protocol-validator
  -----------------------------------------------------------------------------

## Design Principles

-   Independent implementation and validation.
-   Different models whenever feasible.
-   One sandbox and one gateway per agent.
-   Fresh execution context for each new task.
-   Validation evidence is mandatory before publication.
-   ELIS GitHub publishes only validated work.

## Success Criteria

A task is complete only when: 1. The implementer finishes the assigned
work. 2. The validator independently returns PASS. 3. PM accepts the
outcome. 4. ELIS GitHub performs authorised repository actions (if
applicable).