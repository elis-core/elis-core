# ELIS Sandboxed-Agent End-to-End Implementation Runbook

**Date:** 2026-07-07  
**Scope:** End-to-end implementation, configuration, rebuild recovery, and validation of sandboxed ELIS Hermes agents.  
**Pattern source:** sandboxed `elis-pm` validation (2026-07-06), sandboxed `elis-supervisor` configuration (2026-07-07).  
**Target agents:** `elis-supervisor` (current), future SLR agents.

---

## 1. Prerequisites and Hard Constraints

### 1.1 Tooling

- **NemoClaw only** for all sandbox access. Do not use Docker directly.
- Do not use `docker exec`, `docker logs`, `docker inspect`, `docker cp`, or direct container filesystem access.
- All sandbox commands go through `nemoclaw`.

### 1.2 Runtime

- Runtime: Hermes Agent (not OpenClaw).
- Provider: PO-specified (e.g. `nvidia-prod`).
- Model: PO-specified (e.g. `moonshotai/kimi-k2.6`).
- Do not change model/provider during configuration unless PO explicitly approves after stop-and-report.

### 1.3 Nemoclaw exec single-line rule

Commands passed directly to `nemoclaw <sandbox> exec -- ...` must be **single-line command arguments**. Do not pass heredocs, multiline scripts, or embedded newline characters.

Correct:

```bash
nemoclaw elis-pm exec -- bash -lc 'curl -sS http://172.19.0.1:9510/health'
```

Incorrect:

```bash
nemoclaw elis-pm exec -- bash -lc '
curl -sS http://172.19.0.1:9510/health
'
```

### 1.4 Safe multiline script pattern

For non-trivial scripts, create the script on the host, upload it into the sandbox, then execute with a single-line command:

```bash
tar -C /tmp -cf - script.sh | nemoclaw elis-pm exec -- tar -xf - -C /tmp
nemoclaw elis-pm exec -- bash -lc /tmp/script.sh
```

### 1.5 Role boundaries

- Supervisor owns implementation, runtime, bridge, service, policy, gateway, and profile changes — only when explicitly PO-approved.
- Supervisor must not validate own work. Advisor validates.
- PM coordinates only.
- GitHub remote operations remain ELIS GitHub-owned.
- No direct database writes. Use sanctioned CLI/API only.

---

## 2. Rebuild-Safe Recovery Sequence

### 2.1 Before any rebuild

Always create a backup before running `nemoclaw <sandbox> rebuild`.

```bash
SANDBOX=elis-pm
BACKUP_DIR=/tmp/elis-backups/${SANDBOX}-pre-rebuild-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$BACKUP_DIR"

# Create backup archive inside the sandbox
nemoclaw $SANDBOX exec -- bash -lc 'tar -czf /sandbox/backup-pre-rebuild.tar.gz -C /sandbox/.hermes . 2>/dev/null || true'

# Download backup to host
nemoclaw $SANDBOX download /sandbox/backup-pre-rebuild.tar.gz "$BACKUP_DIR/backup-pre-rebuild.tar.gz"

# Record SHA256
sha256sum "$BACKUP_DIR/backup-pre-rebuild.tar.gz" > "$BACKUP_DIR/backup-pre-rebuild.tar.gz.sha256"
cat "$BACKUP_DIR/backup-pre-rebuild.tar.gz.sha256"
```

### 2.2 Backup constraints

- The backup archive must be created under `/sandbox/...` — `nemoclaw download` cannot download from `/tmp`.
- The backup may contain local config/secrets (`.env`, `config.yaml` with credentials). **Do not share.**
- Store backups in a secure host location.

### 2.3 After rebuild

After any `nemoclaw rebuild` or `nemoclaw onboard --recreate-sandbox`:

1. The sandbox is reset to default Hermes skeleton state.
2. All custom profile files, policies, skills, and `.env` must be restored.
3. Gateway must be restarted or reconnected.
4. Full post-rebuild acceptance checklist (Section 7) must be run.

---

## 3. Repo-First Restoration After Rebuild

### 3.1 Canonical source of truth

The canonical source for all durable profile files is the `elis-core` repository:

```text
/opt/elis/repo/profiles/hermes/<agent-name>/
```

**Do not restore from memory, from another sandbox, or from Obsidian notes.** Restore only from the canonical repo.

### 3.2 Required restoration files

| File | Required | Notes |
|---|---|---|
| `AGENTS.md` | Yes | Role identity and authority boundaries |
| `SOUL.md` | Yes | Identity and hard limits |
| `SKILLS.md` | Yes | Operational skills and procedures |
| `ENVIRONMENT.md` | Yes | Environment keys and bridge configuration |
| `profile.yaml` | Yes | Runtime binding description |
| `channel_directory.json` | Yes (if present) | Discord channel registrations |
| `config.runtime.template.yaml` | If present | Sanitized config reference template |
| Shared skills (`_shared/skills/`) | Yes | Especially `host-kanban-a2a-bridge-readonly/SKILL.md` |

### 3.3 Restoration command pattern

```bash
REPO=/opt/elis/repo
AGENT=elis-supervisor
PROFILE_DIR=profiles/hermes/$AGENT

for f in AGENTS.md SOUL.md SKILLS.md ENVIRONMENT.md profile.yaml channel_directory.json config.runtime.template.yaml; do
  if [ -f "$REPO/$PROFILE_DIR/$f" ]; then
    nemoclaw $AGENT upload "$REPO/$PROFILE_DIR/$f" "/sandbox/.hermes/$f"
    echo "OK: $f"
  else
    echo "MISSING: $f (not in canonical repo)"
  fi
done

# Shared skills
nemoclaw $AGENT upload \
  "$REPO/profiles/hermes/_shared/skills/host-kanban-a2a-bridge-readonly/SKILL.md" \
  "/sandbox/.hermes/skills/elis/host-kanban-a2a-bridge-readonly/SKILL.md"
```

### 3.4 SHA256 verification after restoration

Canonical (host):

```bash
sha256sum $REPO/$PROFILE_DIR/AGENTS.md $REPO/$PROFILE_DIR/SOUL.md $REPO/$PROFILE_DIR/SKILLS.md $REPO/$PROFILE_DIR/ENVIRONMENT.md $REPO/$PROFILE_DIR/profile.yaml
```

Sandbox:

```bash
nemoclaw $AGENT exec -- bash -lc 'sha256sum /sandbox/.hermes/AGENTS.md /sandbox/.hermes/SOUL.md /sandbox/.hermes/SKILLS.md /sandbox/.hermes/ENVIRONMENT.md /sandbox/.hermes/profile.yaml'
```

All hashes must match. Report any mismatches or missing files — do not assume.

---

## 4. Runtime-Only Data Boundaries

### 4.1 Not canonical repo data

These files are runtime-generated or credential-bearing and **must not be committed** to the canonical repo:

| File | Why |
|---|---|
| `/sandbox/.hermes/.env` | Contains secrets (tokens, API keys) |
| `API_SERVER_KEY` | Runtime-generated per sandbox |
| Raw Discord tokens | `DISCORD_BOT_TOKEN` — credential, not code |
| OpenShell/NemoClaw credential bindings | Managed by NemoClaw, not ELIS governance |
| Generated gateway locks/PIDs | `gateway.lock`, `gateway.pid` — ephemeral |
| Live forwards | Port forwards managed by NemoClaw |
| Active sandbox policy state | Managed by NemoClaw/OpenShell |
| Runtime/state DBs | `state.db`, `kanban.db`, `response_store.db` |

### 4.2 Must not be guessed or committed

If a file is in this category and missing from the sandbox, **do not fabricate it**. Report it as missing and request PO guidance.

---

## 5. Secret-Boundary Rules

### 5.1 Credential storage

- Do **not** store raw `DISCORD_BOT_TOKEN` in `/sandbox/.hermes/.env` if an approved credential mechanism exists.
- Use the governed resolver/credential mechanism (e.g. `openshell:resolve:env:DISCORD_BOT_TOKEN`) if that is the active approved mechanism.
- Provider credentials (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, etc.) must go through the approved credential mechanism, not in `.env`.

### 5.2 .env constraints

- Keep `API_SERVER_PORT=8642`.
- Remove `API_SERVER_ENABLED` from `.env` if it triggers NemoClaw/Hermes secret-boundary checks.
- Required `.env` keys for Discord (values supplied through credential mechanism):
  ```
  DISCORD_BOT_TOKEN
  DISCORD_ALLOWED_USERS
  DISCORD_HOME_CHANNEL
  DISCORD_ALLOWED_CHANNELS
  DISCORD_REQUIRE_MENTION
  DISCORD_FREE_RESPONSE_CHANNELS
  DISCORD_ALLOW_BOTS
  ```

### 5.3 Secret output rule

- Never print raw secrets in logs, reports, or terminal output.
- When verifying `.env`, report keys only (e.g. `DISCORD_BOT_TOKEN=SET`) — never values.
- Use `***REDACTED***` for any output that might contain secrets.

### 5.4 Do not migrate blindly

Do not copy these from a host or non-sandboxed profile into the sandbox or repo:

```text
.env
.env.bak*
config.yaml.bak*
```

---

## 6. Custom Kanban/A2A Bridge Policy Restoration

### 6.1 Policy loss on rebuild

`nemoclaw rebuild` or `onboard --recreate-sandbox` will drop custom policy preset registrations. Network policies applied through `nemoclaw policy-add --from-file` are not preserved.

### 6.2 Detecting missing custom presets

```bash
nemoclaw $AGENT policy-list
```

If custom presets (e.g. `elis-kanban-a2a-bridge-readonly-ip`) are missing, they must be restored.

### 6.3 Reviewed safe policy scope

All custom bridge policies target:

```text
host: 172.19.0.1
allowed_ips: 172.19.0.1/32
port: 9510
```

Do not use `host.openshell.internal:9510` — it causes policy/SSRF issues.

#### Policy 1: Read-only bridge access

```yaml
name: elis-kanban-a2a-bridge-readonly-ip
endpoint: 172.19.0.1:9510
allowed_ips: [172.19.0.1/32]
rules:
  - method: GET
    paths:
      - /health
      - /kanban/identity
      - /kanban/status-counts
      - /a2a/status
```

#### Policy 2: Kanban canary write

```yaml
name: elis-kanban-a2a-bridge-kanban-canary-write
endpoint: 172.19.0.1:9510
allowed_ips: [172.19.0.1/32]
rules:
  - method: POST
    paths:
      - /kanban/canary-create
      - /kanban/canary-comment
      - /kanban/canary-close
```

#### Policy 3: A2A canary send

```yaml
name: elis-kanban-a2a-bridge-a2a-canary-send
endpoint: 172.19.0.1:9510
allowed_ips: [172.19.0.1/32]
rules:
  - method: POST
    paths:
      - /a2a/canary-send
```

### 6.4 Applying policies

Create each policy as a YAML file on the host, then apply:

```bash
nemoclaw $AGENT policy-add --from-file /tmp/policy-name.yaml --yes
```

### 6.5 Policy review warning

NemoClaw warns: **"custom preset targets are not vetted. Review hosts before applying."**

Before applying any custom policy:

1. Verify the host IP and port are correct.
2. Verify the allowed IP range is the minimum necessary.
3. Verify the method/path rules are the minimum necessary.
4. Do not use broad `access: full` where REST rules are sufficient.

---

## 7. Post-Rebuild Acceptance Checklist

After any rebuild, recreate, or major configuration change, run every check in this list.

### 7.1 Sandbox health

```bash
nemoclaw $AGENT status
nemoclaw $AGENT connect --probe-only
```

Expected: `Phase: Ready`, `Connected: yes`.

### 7.2 Hermes gateway listener

```bash
nemoclaw $AGENT exec -- bash -lc 'ss -tlnp 2>/dev/null | grep 8642 || netstat -tlnp 2>/dev/null | grep 8642'
```

Expected: listener on port `8642`.

### 7.3 Profile file inventory

```bash
nemoclaw $AGENT exec -- bash -lc 'ls -la /sandbox/.hermes/AGENTS.md /sandbox/.hermes/SOUL.md /sandbox/.hermes/SKILLS.md /sandbox/.hermes/ENVIRONMENT.md /sandbox/.hermes/profile.yaml'
```

All five files must exist.

### 7.4 SHA256 canonical vs sandbox

Run canonical and sandbox SHA256 (Section 3.4). All must match.

### 7.5 .env keys-only check

```bash
nemoclaw $AGENT exec -- bash -lc 'grep -E "^[A-Z_]+=" /sandbox/.hermes/.env | sed "s/=.*/=***REDACTED***/"'
```

Verify required keys present, no values exposed.

### 7.6 Policy list

```bash
nemoclaw $AGENT policy-list
```

Verify all required policies are active.

### 7.7 Host bridge checks from sandbox

```bash
nemoclaw $AGENT exec -- bash -lc 'curl -sS -m 8 http://172.19.0.1:9510/health'
nemoclaw $AGENT exec -- bash -lc 'curl -sS -m 8 http://172.19.0.1:9510/kanban/identity'
nemoclaw $AGENT exec -- bash -lc 'curl -sS -m 8 http://172.19.0.1:9510/kanban/status-counts'
nemoclaw $AGENT exec -- bash -lc 'curl -sS -m 8 http://172.19.0.1:9510/a2a/status'
```

### 7.8 Authoritative board verification

- `/kanban/identity` must return `board: elis-core`.
- `/kanban/status-counts` must return nonzero task counts.
- Sandbox-local Kanban is **not authoritative**.

### 7.9 No direct DB writes

Verify no direct database write operations occurred during configuration.

### 7.10 A2A canary (if within approved diagnostic scope)

```bash
nemoclaw $AGENT exec -- bash -lc 'curl -sS -m 90 -w "\nHTTP_STATUS=%{http_code}\n" -X POST http://172.19.0.1:9510/a2a/canary-send -H "content-type: application/json" --data ""'
```

Expected: `HTTP_STATUS=200`, `OK=True`.

---

## 8. Nemoclaw Command Discipline

### 8.1 Allowed command patterns

Run a single command inside the sandbox:

```bash
nemoclaw $AGENT exec -- bash -lc 'single-line-command'
```

Upload a file:

```bash
nemoclaw $AGENT upload /host/path /sandbox/path
```

Download a file:

```bash
nemoclaw $AGENT download /sandbox/path /host/path
```

Inspect sandbox status:

```bash
nemoclaw $AGENT status
```

Inspect sandbox logs:

```bash
nemoclaw $AGENT logs --tail 120
```

### 8.2 Prohibited patterns

Do not use:

```bash
docker exec ...
docker cp ...
docker inspect ...
docker compose exec ...
```

Do not edit files through direct container filesystem writes, bind-mount edits, or Docker volume manipulation.

### 8.3 Rationale

`nemoclaw` is the governed sandbox control plane. Using `nemoclaw` preserves sandbox boundary, auditability, policy enforcement, runtime identity, and repeatable operational procedure.

---

## 9. Discord and Messaging Configuration

### 9.1 Channel directory

The canonical `channel_directory.json` registers Discord channels the agent may communicate with.

Example for `elis-pm`:

```json
{
  "platforms": {
    "discord": [
      {"id": "1485030292690309132", "name": "elis-pm", "guild": "ELIS", "type": "channel"},
      {"id": "1502602267931578378", "name": "elis-advisor", "guild": "ELIS", "type": "channel"},
      {"id": "1513458363202011256", "name": "elis-ideas", "guild": "ELIS", "type": "channel"}
    ]
  }
}
```

### 9.2 Discord policy

Apply the `discord` policy preset for Discord API access:

```bash
nemoclaw $AGENT policy-add discord --yes
```

### 9.3 Credential configuration

Discord credentials (`DISCORD_BOT_TOKEN`, etc.) must be configured through the approved credential mechanism for the sandbox. Do not paste raw tokens into the repo.

### 9.4 Explicit send requirement

Natural-language "post to another channel" is not sufficient. The agent must use an explicit outbound send mechanism:

```bash
hermes send --to "discord:#channel-name" "<message>"
```

---

## 10. Authoritative Kanban and A2A Rules

### 10.1 Board authority

- Authoritative board: **only `elis-core`**.
- Authoritative path: host bridge / `hermes kanban --board elis-core`.
- Sandbox-local Kanban is disabled/non-authoritative.
- Do not copy or mount the host Kanban database into the sandbox.

### 10.2 Mutation rules

- No direct SQLite/database writes.
- Kanban mutations only through sanctioned Hermes Kanban CLI/API.
- A2A delivery only through official A2A SDK / localhost JSON-RPC `/a2a`.
- Bridge/helper code must never issue direct DB write operations.

### 10.3 Kanban canary endpoints

These are diagnostic-only endpoints for controlled validation:

```text
POST /kanban/canary-create
POST /kanban/canary-comment
POST /kanban/canary-close
```

Every canary run must use a unique `run_id` and unique idempotency key.

### 10.4 A2A canary endpoint

```text
POST /a2a/canary-send
```

This is a diagnostic canary endpoint, not a general production dispatch endpoint.

### 10.5 A2A service ports

```text
9500 -> ELIS Advisor
9501 -> ELIS Supervisor
9502 -> ELIS PM
9503 -> ELIS GitHub
```

A2A communication goes through official A2A SDK → localhost JSON-RPC `/a2a`. There is no Hermes A2A CLI command.

---

## 11. Future Production Policy Note

### 11.1 Canary vs production policies

- **Keep canary policies** for diagnostics until production policies are implemented and validated.
- **Do not rename** canary policies into production.
- Create **separate minimal production policies** later.

### 11.2 Planned production policy names

```text
elis-kanban-a2a-bridge-pm-kanban-coordination
elis-kanban-a2a-bridge-pm-a2a-coordination
```

### 11.3 Production policy governance

- Production policies must be **Supervisor-implemented**.
- Production policies must be **Advisor-validated**.
- Production policies must be **PO-approved** before activation.
- Do not activate production policies during diagnostic/canary phase.

---

## 12. Commit and Validation Sequence

### 12.1 Scoped commits

When canonical repo profile files change, use a scoped local commit:

```bash
cd /opt/elis/repo
git add profiles/hermes/$AGENT/AGENTS.md \
        profiles/hermes/$AGENT/SOUL.md \
        profiles/hermes/$AGENT/SKILLS.md \
        profiles/hermes/$AGENT/ENVIRONMENT.md \
        profiles/hermes/$AGENT/profile.yaml
git diff --cached --name-status
git commit -m "governance: synchronize sandboxed $AGENT profile files"
```

Only stage files in the approved scope. Do not stage unrelated files.

### 12.2 Advisor validation must confirm

- Commit scope is limited to approved files.
- Canonical files contain required role and board-binding rules.
- Active sandbox files match canonical SHA256.
- Agent inventory uses host bridge and returns nonzero `elis-core` counts.
- No direct DB writes occurred.
- No bridge/gateway/service/policy changes occurred unless separately approved.

### 12.3 Remote GitHub operations

Remain out of scope unless PO authorizes ELIS GitHub to push or open/update a PR.

---

## Appendix A — Nemoclaw Command Quick Reference

| Operation | Command |
|---|---|
| Sandbox status | `nemoclaw <name> status` |
| Health check | `nemoclaw <name> doctor --json` |
| Probe connectivity | `nemoclaw <name> connect --probe-only` |
| List policies | `nemoclaw <name> policy-list` |
| Add custom policy | `nemoclaw <name> policy-add --from-file <path> --yes` |
| Upload file | `nemoclaw <name> upload <host-path> <sandbox-path>` |
| Download file | `nemoclaw <name> download <sandbox-path> <host-path>` |
| Single command | `nemoclaw <name> exec -- bash -lc '<cmd>'` |
| Logs | `nemoclaw <name> logs --tail 200` |
| Rebuild | `nemoclaw <name> rebuild --yes --verbose` |
| Destroy | `nemoclaw <name> destroy --yes --no-cleanup-gateway` |
| Onboard Hermes | `nemoclaw onboard --name <name> --agent hermes --yes --non-interactive --yes-i-accept-third-party-software` |
| Recreate sandbox | `nemoclaw onboard --recreate-sandbox --name <name> --agent hermes --yes --non-interactive --yes-i-accept-third-party-software` |

---

## Appendix B — Agent-Specific Profile File Checklist

For each sandboxed ELIS agent, verify these files exist in both canonical repo and active sandbox:

- [ ] `AGENTS.md` — role identity and authority boundaries
- [ ] `SOUL.md` — identity and hard limits
- [ ] `SKILLS.md` — operational skills and procedures
- [ ] `ENVIRONMENT.md` — environment keys and bridge configuration
- [ ] `profile.yaml` — runtime binding description
- [ ] `channel_directory.json` — Discord channel registrations (if applicable)
- [ ] `config.runtime.template.yaml` — sanitized config reference (if applicable)
- [ ] Shared skills installed under `/sandbox/.hermes/skills/`
- [ ] `host-kanban-a2a-bridge-readonly/SKILL.md` installed

---

## Appendix C — Host Bridge Architecture

```text
sandboxed ELIS agent
  -> NemoClaw/OpenShell governed REST policy
  -> 172.19.0.1:9510 host bridge
  -> sanctioned host Hermes Kanban CLI/API and official A2A SDK
  -> authoritative elis-core Kanban board and localhost A2A services
```

- Bridge service: `elis-kanban-a2a-bridge.service`
- Bridge bind: `172.19.0.1:9510`
- Repo capture: `ops/kanban-a2a-bridge/bridge.py`
- Sandbox source IP (observed): `172.19.0.2`
- A2A ports: `9500` (Advisor), `9501` (Supervisor), `9502` (PM), `9503` (GitHub)