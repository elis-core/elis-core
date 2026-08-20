# ELIS Temporal Provenance Model

T2, directive section 16. Source: `src/elis_temporal/provenance/model.py`. Tests: `tests/unit/test_provenance.py` (4/4 passing).

## The boundary

**Temporal's own Event History is authoritative execution/control-state provenance.** Every Activity call and result, every Signal/Update, every retry attempt, every state transition of every Workflow this project builds is already durably recorded there by Temporal itself, queryable via the standard Temporal client/CLI/UI. This project does not — and per this document, must not — recreate that as a second ELIS-side state machine. `GatedPipelineWorkflow`'s own `stage` query is a convenience projection for callers/tests, not a competing source of truth; if it ever disagreed with the real Event History, the Event History would be right.

**ELIS immutable artifacts are a separate concern**: implementation evidence, validation evidence, security evidence, scientific evidence, host-operation evidence where separately required. This is the same category of thing `kanban_evidence.py` (Hermes P2 remediation, `d5e5977e2f`) already manages on the Hermes/Kanban side — append-only evidence, plus a separate mutable canonical-pointer structure keyed by `(subject, evidence_class, scope)`. This T2 module reuses that shape as a **pattern**, not as imported code: this project's Adapter boundary deliberately shells out to the `hermes` CLI rather than importing `hermes_cli` internals (see `adapter.py`'s docstring for why — internal modules are not Hermes's stable contract), so `provenance/model.py` is an independent, minimal implementation of the same idea for the Temporal side.

## What's built: a pointer, not a store

```python
ProvenanceRecord(workflow_id, run_id, evidence_class, artifact_ref, sha256=None)
```

A frozen dataclass connecting a Temporal execution (`workflow_id` + `run_id` — both required; a `ProvenanceRecord` without an execution pointer is rejected as `InvalidProvenanceRecord`, since provenance without a pointer to what happened isn't provenance) to an evidence artifact (`artifact_ref` — a path, URL, or other stable locator; this module does not interpret it) and, optionally, a `sha256` digest (validated as a 64-character lowercase hex string when present, not merely accepted as an opaque string). `evidence_class` is a free-text field naming which of the five evidence categories above the record represents — not an enum, since the concrete set of evidence classes an ELIS Workflow needs is expected to grow with T3/T4 usage and a closed enum would need editing here every time.

## "Evidence is immutable; current authority may evolve separately"

`ProvenanceRecord` is a frozen dataclass — once constructed, a record cannot be mutated. This mirrors `kanban_evidence.py`'s append-only-evidence half. The other half — a *mutable canonical pointer* saying "which run/record is currently authoritative for a given logical unit of work" — is deliberately **not** built as a competing structure here: that role is already filled by [the Workflow Identity Policy](ELIS-TEMPORAL-WORKFLOW-IDENTITY-POLICY.md)'s semantic-ID scheme (a given `(domain, process, semantic_key)` has at most one current open/authoritative Workflow run at a time, by Temporal's own ID-uniqueness guarantee) — a second, ELIS-side "canonical pointer" table would just be a duplicate, error-prone source of truth for something Temporal already tracks natively.

## Deferred / not built in T2

- **No storage/persistence layer.** `provenance/model.py` only builds and validates the record type; nothing here writes a `ProvenanceRecord` to disk, a database, or attaches it to a real Workflow/Activity result. Wiring evidence-recording calls into `GatedPipelineWorkflow` (e.g. attaching a `ProvenanceRecord` to the validator's PASS result) is a real T3/T4 integration task, not attempted here — no concrete evidence-artifact-generation requirement existed in T2 to wire it against.
- **No query/lookup API.** There is no `find_provenance_records_for(workflow_id=...)`-style function — this pass only proves the record type is well-formed, not a retrieval system.
- **No cross-reference to Hermes/Kanban's own evidence records.** A future integration might want a `ProvenanceRecord` that can point at (not duplicate) a `kanban_evidence.py` entry — not built, no concrete requirement specified the linkage shape.
