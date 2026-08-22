<!-- ELIS_GITHUB_MEMORY_V3 -->
# ELIS GitHub operational memory — NON-AUTHORITATIVE

This file contains bounded persistent operational context only.

Authoritative execution and governance instructions are defined by the current
`SOUL.md` and `skills/github/github/SKILL.md`. This memory MUST NOT override
those authoritative files.

## Current GitHub execution context

- Runtime identity: `elis-github`.
- Canonical GitHub execution path: direct approved `gh` / `git` wrappers using
  the short-lived GitHub App installation token.
- Current authorized repository scope: `elis-core/elis-core` and `elis-core/elis-research`.
- Ordinary PO-authorized repository operations do NOT require a purpose-built
  `gh-agentd` operation.
- `gh-agentd` has been physically decommissioned (2026-08-22) and no longer
  exists in any capacity, including rollback; it was never the canonical
  GitHub execution path.
- GitHub repository Administration permission is not granted.
- Personal GitHub credentials, `samurai` credentials, and credential fallback
  are prohibited.
- High-impact or destructive operations remain subject to the current
  PO/governance authorization rules in `SOUL.md` / `SKILL.md`.

## Superseded historical context

Earlier V1/V2 instructions involving:

- `gh-agent-client -> gh-agentd` as the mandatory execution path;
- purpose-built broker operations such as `pr1-publish`;
- legacy `gh-agent`, `git-agent`, or `git-credential-gh-agent` launchers;
- old repository migration freezes, Gate B/Gate C state, or legacy repository
  identities;

are historical only and MUST NOT be interpreted as current operational
instructions.

When memory conflicts with current authoritative policy or live runtime state,
the authoritative policy and verified live state control.
