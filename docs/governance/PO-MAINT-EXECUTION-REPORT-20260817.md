# PO MAINTENANCE EXECUTION REPORT — HERMES v0.20.2
# HOST-SIDE APPLICATION COMPLETE — RELEASE POST-UPDATE HMP

**PO directive received 2026-08-17.** Source: PO Carlos Rocha, delivered via Discord. This is the authoritative record of the host-side Hermes v0.20.2 live maintenance execution and the release of the POST-UPDATE HMP gate (t_df6b556c).

## 1. AUTHORIZED HERMES CANDIDATE
- Live Hermes source: `5600de8c00eaf3d49f462d1325881ba33754c0da`
- `Hermes Agent v0.20.2 (2026.8.16)`, local `5600de8c` (+16 carried commits)
- Live source tree: CLEAN

## 2. CONFIG / DEPENDENCY APPLICATION
- Dependency installation: PASS
- Shared config migration: PASS → `_config_version=37`
- 36/36 profile config migrations: PASS → all `_config_version=37`
- Post-migration import / compile / doctor validation: PASS

## 3. LIVE SERVICE TOPOLOGY
ACTIVE:
- hermes-gateway-elis-ideas.service
- hermes-gateway-elis-pm.service
- hermes-gateway-elis-research.service
- hermes-gateway-elis-advisor.service
- hermes-gateway-elis-supervisor.service
- hermes-dashboard.service

Separate isolated system-level runtime:
- hermes-gateway-elis-github.service = ACTIVE (user=elis-github, runtime under the isolated elis-github Hermes worktree, untouched by user-level Hermes update)

INTENTIONALLY INACTIVE / DISABLED:
- hermes-gateway.service (generic gateway deliberately retired after live inspection confirmed it would duplicate Kanban-dispatch capability)

## 4. SINGLE-DISPATCHER CORRECTION
Three dispatcher-capable configs found before correction: shared/default=true, elis-pm=true, elis-research=true.
Bounded host-side correction applied and verified:
- shared/default = false
- elis-ideas = false
- elis-pm = true
- elis-research = false
- elis-advisor = false
- elis-supervisor = false

Current temporary sole mechanical dispatcher: **ELIS PM**. Generic gateway disabled + inactive. Research gateway restarted after correction, remains healthy.
NOTE: intentional maintenance deviation from live evidence, not hidden failure. PO separately approved future `elis-dispatcher` architecture — NOT implemented as part of HMP/HMV.

## 5. POST-UPDATE CANARIES (all PASS)
1. ELIS Ideas — PASS (direct non-mutating runtime invocation)
2. ELIS PM — PASS (real native Kanban dispatch, exactly one run, claim lock matched PM gateway PID, no duplicate)
3. ELIS Research — PASS (cross-board single-dispatcher proven; worker PPID + cgroup = PM gateway, exactly one run)
4. ELIS Advisor — PASS (exactly one run, correct profile, exact run-summary marker, config unchanged after migration to v37)
5. ELIS Supervisor — PASS (packet-only/no-action, exactly one run, correct profile/board, config unchanged, no host/root mutation)
6. ELIS GitHub — PASS security-critical (broker path /run/gh-agentd absent → github_app_credential declared=true authorized=true available=false executable=false → WAITING_FOR_CAPABILITY; GH_TOKEN fallback BLOCKED; PM GitHub fallback BLOCKED; rejected GitHub activity invokes Hermes FALSE; real GitHub mutation NONE; isolated gateway PID unchanged)

## 6. TEMPORAL ↔ HERMES LIVE COMPATIBILITY
- Accepted Temporal T2: `7c346445ec83842550bdfb1bee9e2fb24a3521bf`
- Temporal runtime: temporal/app/.venv/bin/python, Python 3.11.15, temporalio 1.31.0
- Live Hermes resolved explicitly to: hermes-agent/.venv/bin/hermes
- Live Adapter test under ACTUAL Temporal Python: STATUS=completed, STRUCTURED_RESULT=TEMPORAL_RUNTIME_HERMES_V0202_OK, FAILURE_CLASS=None → TEMPORAL_RUNTIME_LIVE_ADAPTER=PASS
- Authoritative Temporal T2 regression: **105 passed in 31.27s, 0 failed, 105 collected**
- Temporal dev server: 127.0.0.1:7233 LISTENING (dev-server default ports)
- Verdict: TEMPORAL T2 ↔ HERMES v0.20.2 COMPATIBILITY: **PASS**; T2 tree clean at exact accepted SHA

## 7. KNOWN RESIDUALS / FOLLOW-ON (NOT grounds to reopen; must be recorded accurately)
- **A. SQLite runtime** — Hermes Python linked to SQLite 3.50.4; Hermes POSIX-lock safety fix present+verified → accepted non-blocking residual; separate SQLite runtime-hardening assessment being prepared; no SQLite change authorized during HMP/HMV.
- **B. Dedicated dispatcher** — PO approved elis-dispatcher = future sole mechanical dispatcher (elis-dispatcher=true, elis-pm=false, elis-research=false, others=false, generic disabled). Separate post-maintenance initiative; not during HMP/HMV.
- **C. auto_decompose** — configs still auto_decompose=true; PO target auto_decompose=false. Handle in separate dispatcher-topology normalization gate.
- **D. Temporal GitHub execution-context metadata** — accepted T2 contains stale assumption that elis-github has no persistent gateway; live reality has isolated system-level persistent elis-github gateway. Did not affect capability fail-closed canary. Bounded Temporal metadata correction required before T3; do NOT modify accepted T2 during HMP/HMV.
- **E. Adapter operational harness** — initial ad-hoc smoke invocation used wrong Python import env (did not execute Adapter); corrected and rerun under explicit Temporal Python runtime → PASS. Do not treat first harness failure as Adapter defect.

## 8. HMP AUTHORIZATION
PO authorizes running **t_df6b556c** POST-UPDATE HMP against the ACTUAL live state.
HMP must independently verify live evidence and explicitly account for authorized/live-evidence deviations: generic gateway intentionally retired; single-dispatcher normalization; PM temporarily sole dispatcher; six canaries; live Temporal Adapter PASS; Temporal 105/105 PASS.
- Do not normalize discrepancies silently.
- If HMP PASS: release the existing HMV gate to ELIS Advisor (t_ce67ccd6).
- If HMP discovers a genuinely new material defect: STOP and report only that bounded defect.

## 9. HMV SEQUENCE
On HMP PASS, release Advisor POST-UPDATE HMV. HMV must independently validate: actual live candidate + clean provenance; dependency/config migration; service topology; exactly-one dispatcher invariant; Research cross-board semantics; all six canaries; GitHub fail-closed security; Temporal Adapter compatibility; 105/105 Temporal regression; no unauthorized T3/T4 or production Temporal cutover. After HMV: STOP and return to PO.
Neither HMP nor HMV authorizes T3.

## 10. BINDING SEQUENCE
Host-side maintenance execution COMPLETE ✅ | Six post-update canaries PASS ✅ | Temporal live Adapter PASS ✅ | Temporal authoritative suite 105/105 PASS ✅
→ PM POST-UPDATE HMP → Advisor POST-UPDATE HMV → STOP → PO final Hermes maintenance acceptance.

No T3/T4. No Temporal production authority. No Kanban cutover. No dispatcher-topology implementation yet. No SQLite runtime mutation yet.