# TEMPORAL-I1 T3 — GitHub V3 Execution-Path Reconciliation

Purpose: durably reconcile historical candidate GitHub-execution
documentation (which self-describes as not yet installed) with the
confirmed-live V3 execution architecture, so that any future T3-G1
(GitHub publication representative workflow) implementation binds to the
real current execution path rather than a stale or superseded assumption.

This document records evidence gathered 2026-08-20. It does not modify any
deployed configuration, service, or ticket.

## GitHub V3 live-binding evidence

`GITHUB_V3_LIVE_BINDING=CONFIRMED_LIVE`

- **Runtime identity**: uid 995 / gid 983, principal `elis-github`.
- **System unit**: `hermes-gateway-elis-github.service` — a genuine
  system-level (not user-session) systemd unit, `FragmentPath=
  /etc/systemd/system/hermes-gateway-elis-github.service`, running
  `hermes_cli.main --profile elis-github gateway run`. Confirmed started
  2026-08-19 14:04:15 BST.
- **Current repository scope**: exactly two repositories —
  `elis-core/elis-core` and `elis-core/elis-research` — confirmed via the
  live deployed scope config plus a real, successfully-completed
  `REPOSITORY_SCOPE_EXACT=PASS` gate observed in the token-refresh log.
- **Current canonical execution model**: approved direct `gh`/`git` path
  under `/usr/local/libexec/elis-github/` (including a restricted
  `wrappers/` subdirectory, root:elis-github, mode 750) using short-lived
  GitHub App installation credentials, refreshed on a live
  `elis-github-token-refresh.timer` (~10-minute interval). A real successful
  mint was observed with `INSTALLATION_IDENTITY=PASS`,
  `REPOSITORY_SCOPE_EXACT=PASS`.
- **Empirical confirmation**: two real merges via this path —
  `elis-core/elis-research#10` (merged 2026-08-19T14:14:10Z) and
  `elis-core/elis-core#9` (merged 2026-08-19T22:03:07Z), both authored by
  `elis-github[bot]`, both consistent with the gateway's 14:04:15 start
  time and the two-repository scope above.

## gh-agentd role

`GH_AGENTD_ROLE=DECOMMISSIONED` (current state)

The following paragraph describes the historical state as of 2026-08-20,
when gh-agentd was still present as rollback infrastructure:

> `GH_AGENTD_ROLE=ROLLBACK_ONLY` (historical, 2026-08-20)
>
> `/etc/elis/gh-agentd.acl.yaml` was unchanged since 2026-08-15: single-repo
> read-only-only allowlist (`elis-core/elis-research` only — narrower than
> the V3 two-repo scope), explicit `prohibited_operations` including
> `push`/`pr-create`/`merge`, with its one write exception gated closed by
> default for a separate, unrelated, frozen branch. The two confirmed merges
> above went through the new standalone gateway + token-wrapper path
> entirely, never through gh-agentd. gh-agentd's rollback-only status was
> therefore evidenced, not merely asserted.

As of the completed GH-AGENTD physical decommission (recorded separately
after 2026-08-20), this historical state is superseded:

- **`GH_AGENTD_PHYSICAL_DECOMMISSION=COMPLETE`**: gh-agentd has been
  physically decommissioned and is unavailable.
- **`GH_AGENTD_ACL_REMOVED=YES`**: `/etc/elis/gh-agentd.acl.yaml` has been
  removed.
- **`GH_AGENTD_EXTENSION_NEVER_IMPLEMENTED=YES`**: the gh-agentd-extension
  mechanism contemplated by `t_5d9a121f` was never implemented.
- The underlying GitHub-write requirement was superseded by the standalone
  V3 elis-github gateway + short-lived GitHub App execution path, which
  remains the live canonical execution path.
- `t_5d9a121f` itself is **not modified** by this reconciliation.

## `t_5d9a121f` reconciliation

`T_5D9A121F_CLASSIFICATION=SUPERSEDED_HISTORICAL_BLOCKER`

This ticket's original acceptance criterion required elis-github to gain
push/PR capability **via an extension of gh-agentd itself** (scoped ACL
extension + kanban-dispatch cgroup rerouting), per the 2026-08-16 Option-A
plan. That specific mechanism was never built — gh-agentd remains
unmodified and read-only, as recorded above. The underlying problem
(elis-github needs a working, correctly-scoped write path) has instead been
solved by a different, separately deployed mechanism: the standalone
`hermes-gateway-elis-github.service` + short-lived-token path described
above, empirically proven by two real merged PRs.

The ticket's literal acceptance criterion is therefore obsolete, but this
document does not close, comment on, or otherwise modify the ticket —
reconciling/closing `t_5d9a121f` is a PM/PO action, not performed here.

## Documentation-lag residual

`DOCUMENTATION_LAG_RESIDUAL`

`/etc/elis/elis-github-token-repos.conf` is live and deployed (its content
matches the confirmed-live two-repository scope above), but its own header
comment still reads `# CANDIDATE — NOT INSTALLED`. This is a stale
self-description on an otherwise-correct, already-deployed file. It is
recorded here as a known residual only — this document does not edit the
deployed file.

## Summary

| Item | Historical candidate documentation | Confirmed live state (2026-08-20) |
|---|---|---|
| `ELIS_GITHUB_EXECUTION_POLICY_V3.md` | Self-described `CANDIDATE — not yet installed` | Deployed and live |
| Two-repo scope rebase packet | Self-described `STOP BEFORE DEPLOYMENT — nothing installed` | Deployed and live, scope confirmed exact |
| `/etc/elis/elis-github-token-repos.conf` | N/A | Live, deployed, header text stale (see above) |
| gh-agentd | Assumed rollback-only per Option-A framing | Confirmed unmodified, confirmed uninvolved in the two real merges |
| `t_5d9a121f` | Open, blocked, gh-agentd-extension-based fix pending | Superseded by a different mechanism; ticket itself untouched |

Since the completed GH-AGENTD physical decommission, the gh-agentd row on
this summary supersedes to: gh-agentd physically decommissioned and
unavailable; `/etc/elis/gh-agentd.acl.yaml` removed; the gh-agentd-extension
mechanism contemplated by `t_5d9a121f` never implemented; the GitHub-write
requirement carried by the live standalone V3 elis-github gateway +
short-lived GitHub App execution path. (`t_5d9a121f` itself is not modified.)

Any future T3-G1 (GitHub publication representative workflow)
implementation should bind to the confirmed-live execution path described
above — the standalone `elis-github` gateway and short-lived credential
wrapper path — not to the historical gh-agentd/Option-A assumption in the
original T3 plan.
