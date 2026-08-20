"""Provenance boundary (T2, directive section 16).

Temporal's own Event History is authoritative execution/control-state
provenance for every Workflow this project builds -- every Activity
call/result, every Signal/Update, every retry, is already durably recorded
there by Temporal itself. This module does NOT recreate that as a second
ELIS-side state machine.

What it DOES provide: a thin, explicit pointer type connecting a Temporal
execution (workflow_id + run_id) to an ELIS immutable evidence artifact
(implementation evidence, validation evidence, security evidence,
scientific evidence, host-operation evidence) -- conceptually the same
append-only-evidence-plus-mutable-canonical-pointer shape already
established on this platform (`kanban_evidence.py`, Hermes P2
remediation), reused here as a pattern, not imported as code (this
project's Adapter boundary deliberately never imports `hermes_cli`
internals -- see adapter.py's docstring for why).

Evidence itself is immutable once recorded (a `ProvenanceRecord` is a
frozen dataclass); CURRENT workflow/control authority (which Workflow run
is "the" authoritative one for a given logical unit of work) may evolve
independently over time (see policies/workflow_identity.py) -- this module
keeps those two concerns structurally separate rather than conflating
"what happened" with "what currently governs."
"""

from __future__ import annotations

import dataclasses
import re
from typing import Optional

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class InvalidProvenanceRecord(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class ProvenanceRecord:
    workflow_id: str
    run_id: str
    evidence_class: str  # "implementation" | "validation" | "security" | "scientific" | "host_operation"
    artifact_ref: str  # a path, URL, or other stable locator -- this module does not interpret it
    sha256: Optional[str] = None

    def __post_init__(self) -> None:
        if self.sha256 is not None and not _SHA256_RE.match(self.sha256):
            raise InvalidProvenanceRecord(f"sha256={self.sha256!r} is not a lowercase 64-hex-char digest")
        if not self.workflow_id or not self.run_id:
            raise InvalidProvenanceRecord("workflow_id and run_id are both required -- provenance without an execution pointer is not provenance")

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def build_provenance_record(
    *, workflow_id: str, run_id: str, evidence_class: str, artifact_ref: str, sha256: Optional[str] = None
) -> ProvenanceRecord:
    return ProvenanceRecord(
        workflow_id=workflow_id, run_id=run_id, evidence_class=evidence_class, artifact_ref=artifact_ref, sha256=sha256
    )
