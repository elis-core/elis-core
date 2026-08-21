# TEMPORAL-I1 Environment Delta — since `temporal-pilot` discovery

**This file, under `elis-core/elis-core:temporal/docs/`, is the authoritative version, per the PO's 2026-08-20 structural decision migrating all durable TEMPORAL-I1 implementation material into the canonical `elis-core/elis-core` repository (history-preserving import, merge commit `4eb8075f8b2360de15da0ae4021d38fd451514a8`).** The former standalone repository at `/home/samurai/temporal/app` is retained on disk as `ROLLBACK_PROVENANCE_ONLY` — it is not independently maintained going forward and must not be treated as authoritative. Do not edit both; edit only this one.

Everything below is new since the `/home/samurai/temporal-pilot/` discovery documents (2026-08-16, earlier the same day). That discovery did no installation; this pass did.

## Installed / created, this session

| Item | Detail |
|---|---|
| Temporal CLI | v1.8.2, `/home/samurai/temporal/bin/temporal`, SHA256-verified against published checksums |
| Temporal Python SDK | `temporalio` 1.31.0, in isolated venv `/home/samurai/temporal/app/.venv` (Python 3.11.15) |
| Dev server | Running, PID tracked at `/home/samurai/temporal/state/dev-server.pid`, started via the exact args in `deployment/start-dev/start.sh` |
| Namespace | `elis` — registered, confirmed via `temporal operator namespace describe` |
| Persistence file | `/home/samurai/temporal/state/temporal.db` (SQLite, file-backed, survives process restart) |
| Permanent directory tree | `/home/samurai/temporal/{bin,app,config,state,logs,artifacts,deployment,tests,backups,docs}/` per plan §7 |
| Application package | `elis_temporal` — installed editable (`pip install -e .`) in the app venv |

## Measured resource use (idle, dev server + no workers running)

- Confirm before trusting this number for capacity planning under load — it was measured idle, right after startup, not under representative dispatch activity (plan §8.3 explicitly requires load measurement before production authority; this is NOT that measurement, T2-T4/production-hardening's job).
- Process is alive, ports 7233/8233 bound loopback-only (`ss -tlnp` confirmed, not assumed).
- No separate database process running (SQLite is in-process) — this is the resource-light property the plan's §8.2 rationale for choosing `start-dev` over docker-compose predicted; confirmed structurally true (no extra Postgres/Elasticsearch/container process exists), not independently re-measured against the docker-compose alternative (that alternative was never stood up, by design).

## Bind-address confirmation (plan §8.2 required this be verified, not assumed)

`temporal server start-dev --help` on this exact CLI version confirms: `--port` (gRPC frontend) defaults to 7233, `--ui-port` defaults to `--port + 1000` (8233), `--ip`/`--ui-ip` default to `localhost`. Explicit flags were passed anyway (`--ip 127.0.0.1 --ui-ip 127.0.0.1 --port 7233 --ui-port 8233`) rather than relying on defaults, so this remains correct even if a future CLI version changes its defaults.

## Live gateway inventory (re-confirmed this session, not reused from stale discovery)

```
elis-a2a-advisor.service          active running
elis-a2a-github.service           active running   (A2A only — no persistent Hermes gateway for elis-github)
elis-a2a-pm.service                active running
elis-a2a-supervisor.service       active running
elis-litellm-guard.service         active running
elis-litellm.service               active running
hermes-dashboard.service           active running
hermes-gateway-elis-advisor.service    active running
hermes-gateway-elis-ideas.service      active running
hermes-gateway-elis-pm.service         active running
hermes-gateway-elis-research.service   active running
hermes-gateway-elis-slr.service        FAILED / not-found  (known rename fallout, already documented elsewhere)
hermes-gateway-elis-supervisor.service active running
hermes-gateway.service                 active running (generic)
```

## Prerequisite status re-confirmed at the start of this session

- Hermes P2 remediation branch: 13 commits, HEAD `ac6d2ca4bb0a43a72af03f57770be5b681632502`, unchanged, undeployed. Read-only reference only — not touched by this work.
- `t_5d9a121f` (Supervisor's Option-A `gh-agentd` fix, `elis-research` board): still `blocked`. Not resolved during this session. TEMPORAL-I1's own security model inherits this same dependency (see `TEMPORAL-I1-ARCHITECTURE.md`'s execution-context section).

## Provenance statement

**No production Hermes/Kanban/gh-agentd/Option-A mutation occurred.**

This is the precise claim: no file under `/home/samurai/.hermes/`, no live Kanban DB, no systemd unit outside this session's own read-only inventory checks, no `gh-agentd`/credential path, no Discord binding was ever written to. The only external system interaction with a live ELIS profile was one real, deliberate Hermes invocation (`elis-ideas` profile, "Reply with exactly the single word: OK") to prove the Adapter genuinely works — a read-style prompt/response round trip, not a write to any ELIS system of record — logged in `TEMPORAL-I1-ARCHITECTURE.md`'s test evidence.

This does **not** mean no host state changed at all. T0/T1 legitimately created new, non-production host state, authorized and confined to `/home/samurai/temporal/`:

- creation of the `/home/samurai/temporal/` directory tree;
- Temporal CLI download/install (user-space, no root — see `PROVENANCE.md`);
- an isolated Python virtual environment (`app/.venv`);
- a running `temporal server start-dev` process (loopback-only, `127.0.0.1:7233`/`127.0.0.1:8233`);
- creation of the dedicated `elis` Namespace;
- creation/use of file-backed SQLite persistence at the approved Temporal state path (`state/temporal.db`);
- associated local config, log, and artifact files under `/home/samurai/temporal/`.

All of the above is new non-production Temporal-side state, not a mutation of any existing production Hermes/Kanban/gh-agentd/Option-A system.
