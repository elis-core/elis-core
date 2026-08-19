# elis-core

Open AI business management lab for governed multi-agent research and operations.

Canonical repository: `elis-core/elis-core` (this repository). ELIS Research
lives in the separate canonical repository `elis-core/elis-research`.

## Architecture

The accepted ELIS target architecture defines **independent Hermes execution
domains** and an explicit platform control plane. This is an **accepted target
design — not yet implemented**. The authoritative accepted target-design record
is the accepted execution-domain ADR:

`docs/architecture/ADR-20260818-001-ELIS-INDEPENDENT-HERMES-EXECUTION-DOMAINS.md`

### Accepted target design (future state, per the ADR)

- **ELIS Core** — `elis-core/elis-core`; Core orchestration and
  platform/business-management workflows.
- **ELIS Research** — `elis-core/elis-research`; research workflows, including
  **SLR** as a Research subdomain. The former repository identifier
  `elis-core/elis-slr` is **obsolete as a repository name**; the SLR *name*
  remains valid terminology for the Systematic Literature Review workflow.
- **ELIS GitHub** — isolated privileged GitHub execution domain.
- **ELIS Supervisor** — independent platform control plane.
- **Temporal** — durable cross-domain orchestration layer.

### Current state

ELIS agents today share a coordinated lifecycle. The full execution-domain
split, Supervisor independence, Temporal production authority, and the final
dispatcher topology are accepted target decisions and are **not yet
implemented**.
