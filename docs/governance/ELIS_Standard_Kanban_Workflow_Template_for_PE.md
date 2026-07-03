# ELIS Standard Kanban Workflow Template for Production Engineering (PE) v1.0

> **Metadata**  
> **Title:** ELIS Standard Kanban Workflow Template for Production Engineering (PE) v1.0  
> **Repository:** elis-core  
> **Status:** Approved  
> **Version:** 1.0  
> **Last Updated:** 2026-07-03  
> **Owner:** ELIS PM  
> **Approver:** Carlos Rocha (PO)

Purpose: Standard governance workflow for all ELIS PEs.

Workflow:
PM -> Stage 1 Implementation/Evidence -> Stage 2 Independent Validation -> Stage 3 GitHub Publication -> Stage 4 PM Closeout -> PO Decision

Stage 1: Implementer performs approved work and collects evidence.
Stage 2: Independent validator reviews evidence and issues PASS/PASS WITH OBSERVATIONS/FAIL/BLOCKED.
Stage 3: ELIS GitHub commits, pushes and manages PRs after PASS.
Stage 4: PM verifies acceptance criteria and closes out.
Stage 5: PO authorizes completion.

Session policy: Every new implementation and validation task begins with a fresh Hermes/NemoHermes session unless explicitly marked as a continuation.

Example mappings:
- ELIS Core: Supervisor -> Advisor -> ELIS GitHub
- Harvest: Harvest -> Harvest Validator -> ELIS GitHub
- Screening: Screen -> Screen Validator -> ELIS GitHub
- Extraction: Extract -> Extract Validator -> ELIS GitHub
- Synthesis: Synth -> Synth Validator -> ELIS GitHub
- Protocol: Protocol -> Protocol Validator -> ELIS GitHub