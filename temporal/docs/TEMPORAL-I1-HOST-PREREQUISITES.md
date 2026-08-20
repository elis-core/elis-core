# TEMPORAL-I1 Host Prerequisites — T0/T1 phase

## Confirmed: zero root action was needed or used for T0/T1

Every action taken this session (CLI download+install, venv creation, dev-server start, namespace creation) ran as the `samurai` user with no privilege escalation. No `sudo`, no `systemd-run`, no root-owned file touched. This matches the plan's mandated `start-dev` + SQLite approach (§8.2-§8.3) precisely — no Docker daemon start (itself a host action, deliberately avoided), no Postgres install, no new systemd unit.

## `TEMPORAL-HOST-APPLICATION-PACKET`: none produced this phase

No root-required change was identified as necessary for T0/T1. This section exists per plan §16's required format, populated as "none" rather than omitted, so a future session doesn't have to re-derive that this was checked.

## Future root-required items (T0.4 production-hardening territory, NOT requested or attempted now)

Listed for planning visibility only, per plan §8.4 — do not treat as authorized:

1. **PostgreSQL provisioning** — either install a new local instance or isolate a dedicated DB/role in an existing one (none exists on this host currently — confirmed, no `psql`/`pg_ctl` binaries, no postgres package, no postgres systemd unit). Root-required if installed via apt; may be root-optional if a future PO decision allows a user-space Postgres binary instead — worth exploring at that time rather than assumed now.
2. **A persistent systemd unit for the Temporal server**, if it moves beyond a manually-started dev process — this host's existing gateway units are user-level (`~/.config/systemd/user/`), which do NOT require root to create/manage; only a *system*-level unit would. Recommend staying user-level for consistency with existing convention, which would keep this root-free too — flagged as a design choice for whoever does T0.4, not decided here.
3. **Docker daemon start**, only if a future decision reverses this phase's recommendation against the docker-compose bundle — not currently planned, not requested.

## Explicitly NOT prerequisites (common assumptions worth ruling out)

- Opening any firewall/network port beyond loopback — not needed, everything is 127.0.0.1-bound by design.
- Any `gh-agentd`/credential-store change — completely out of scope for T0/T1, and would not be requested even if it were (that's Option-A's territory, see `t_5d9a121f`).
- Any change to a live Hermes gateway's config or unit file — none was touched, none is needed for T0/T1.
