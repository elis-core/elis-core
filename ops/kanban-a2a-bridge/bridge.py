#!/usr/bin/env python3
import json
import os
import re
import socket
import sqlite3
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BIND_HOST = os.environ.get("ELIS_BRIDGE_HOST", "172.19.0.1")
BIND_PORT = int(os.environ.get("ELIS_BRIDGE_PORT", "9510"))
BOARD_PATH = Path(os.environ.get("ELIS_KANBAN_DB", "/home/samurai/.hermes/kanban/boards/elis-core/kanban.db"))
HERMES_BIN = os.environ.get("ELIS_HERMES_BIN", "/home/samurai/.local/bin/hermes")
HOST_HERMES_HOME = os.environ.get("ELIS_HOST_HERMES_HOME", "/home/samurai/.hermes/profiles/elis-pm")
KANBAN_BOARD = os.environ.get("ELIS_KANBAN_BOARD", "elis-core")
A2A_PORTS = [9500, 9501, 9502, 9503]
A2A_REGISTRY_PATH = Path(os.environ.get("ELIS_A2A_REGISTRY", "/opt/elis/local/kanban-a2a-bridge/a2a_bridge_registry.json"))

# --- POST /kanban/create --- production endpoint constants ---
ALLOWED_ASSIGNEES = frozenset({
    "elis-advisor", "elis-supervisor", "elis-pm", "elis-ideas", "elis-github",
})
ALLOWED_INITIAL_STATUSES = frozenset({"ready", "blocked"})
ALLOWED_TOP_LEVEL_KEYS = frozenset({
    "title", "body", "assignee", "initial_status",
    "idempotency_key", "created_by", "parent", "priority", "skill",
})
TITLE_MAX = 500
BODY_MAX = 5000
CREATED_BY_MAX = 64
IDEMPOTENCY_KEY_MAX = 128
CREATED_BY_RE = re.compile(r"^[A-Za-z0-9-]+$")
IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
PARENT_RE = re.compile(r"^t_[A-Za-z0-9]+$")

CANARY_TITLE = "KANBAN_A2A_SANDBOX_PM_CANARY_DO_NOT_USE"
CANARY_KEY_PREFIX = "sandboxed-elis-pm-kanban-a2a-canary"
CANARY_AUTHOR = "sandboxed-elis-pm-canary"

def json_response(handler, status, payload):
    data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json")
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

def read_json_body(handler):
    n = int(handler.headers.get("content-length") or "0")
    if n <= 0:
        return {}
    raw = handler.rfile.read(n)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid JSON body: {exc}") from exc

def open_ro():
    return sqlite3.connect(f"file:{BOARD_PATH}?mode=ro", uri=True)

def kanban_identity():
    if not BOARD_PATH.exists():
        return {"exists": False, "path": str(BOARD_PATH)}
    st = BOARD_PATH.stat()
    with open_ro() as con:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {
        "board": KANBAN_BOARD,
        "exists": True,
        "path": str(BOARD_PATH),
        "size_bytes": st.st_size,
        "mtime_epoch": st.st_mtime,
        "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
        "tables": tables,
        "mode": "read-only-identity"
    }

def status_counts():
    result = {"board": KANBAN_BOARD, "mode": "read-only", "tasks": {}, "task_runs": {}}
    with open_ro() as con:
        for table in ("tasks", "task_runs"):
            cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
            if "status" not in cols:
                continue
            result[table] = {
                str(status): count
                for status, count in con.execute(f"SELECT status, COUNT(*) FROM {table} GROUP BY status ORDER BY status")
            }
    return result

def a2a_status():
    out = {}
    for port in A2A_PORTS:
        ok = False
        err = None
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.5):
                ok = True
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
        out[str(port)] = {"host": "127.0.0.1", "port": port, "tcp_listening": ok, "error": err}
    return {"mode": "read-only", "a2a": out}


def load_a2a_registry():
    if not A2A_REGISTRY_PATH.exists():
        return {
            "ok": False,
            "error": "registry_not_found",
            "path": str(A2A_REGISTRY_PATH),
        }
    try:
        with A2A_REGISTRY_PATH.open("r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception as exc:
        return {
            "ok": False,
            "error": "registry_parse_failed",
            "path": str(A2A_REGISTRY_PATH),
            "message": str(exc),
        }

    if isinstance(registry, dict):
        registry.setdefault("ok", True)
        registry.setdefault("mode", "bridge-mediated-a2a-registry")
        registry.setdefault("path", str(A2A_REGISTRY_PATH))
    return registry


def a2a_registry():
    return load_a2a_registry()


def a2a_agents():
    registry = load_a2a_registry()
    if not registry.get("ok", False):
        return registry

    return {
        "ok": True,
        "mode": "bridge-mediated-a2a-agents",
        "domain_project_managers": registry.get("domain_project_managers", {}),
        "agents": registry.get("agents", {}),
        "hard_prohibitions": registry.get("hard_prohibitions", []),
    }


def a2a_routes():
    registry = load_a2a_registry()
    if not registry.get("ok", False):
        return registry

    return {
        "ok": True,
        "mode": "bridge-mediated-a2a-routes",
        "bridge": registry.get("bridge", {}),
        "raw_host_a2a_ports": registry.get("raw_host_a2a_ports", {}),
        "logical_routes": {
            "elis-pm": {
                "domain": "elis-core",
                "canonical_board": "elis-core",
                "active_runtime": registry.get("domain_project_managers", {}).get("elis-pm", {}).get("active_runtime"),
            },
            "elis-slr": {
                "domain": "elis-slr",
                "canonical_board": "elis-slr",
                "active_runtime": registry.get("domain_project_managers", {}).get("elis-slr", {}).get("active_runtime"),
            },
            "elis-supervisor": {
                "domain": "elis-core",
                "active_runtime": registry.get("agents", {}).get("elis-supervisor", {}).get("active_runtime"),
                "candidate_runtime": registry.get("agents", {}).get("elis-supervisor", {}).get("candidate_runtime"),
                "fallback_runtime": registry.get("agents", {}).get("elis-supervisor", {}).get("fallback_runtime"),
                "cutover_state": registry.get("agents", {}).get("elis-supervisor", {}).get("cutover_state"),
            },
        },
    }


def run_hermes_kanban(args):
    env = os.environ.copy()
    env["HERMES_HOME"] = HOST_HERMES_HOME
    env["HERMES_KANBAN_BOARD"] = KANBAN_BOARD
    env["HERMES_PROFILE"] = "elis-pm"
    cmd = [HERMES_BIN, "kanban", "--board", KANBAN_BOARD] + args
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=40, env=env)
    return {
        "cmd": ["hermes", "kanban", "--board", KANBAN_BOARD] + args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

def extract_task_id(text):
    m = re.search(r"\bt_[A-Za-z0-9]+\b", text or "")
    return m.group(0) if m else None

# ---------------------------------------------------------------------------
# POST /kanban/create — production task creation
# ---------------------------------------------------------------------------

def _sanitise_text(value, max_len=None):
    """Strip control characters; keep printable unicode. Truncate if max_len set."""
    text = str(value or "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    if max_len is not None:
        text = text[:max_len]
    return text

def _error(status, code, **kwargs):
    return {"ok": False, "operation": "kanban_create", "status": status, "error": code, **kwargs}

def _success(status, payload):
    payload.setdefault("ok", True)
    payload.setdefault("operation", "kanban_create")
    return {"status": status, **payload}

def _validate_optional_string(value, max_len, regex, field_name):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if len(s) > max_len:
        return _error(400, f"invalid_{field_name}")
    if regex and not regex.match(s):
        return _error(400, f"invalid_{field_name}")
    return s

def _log_create_event(task_id, assignee, initial_status, has_idempotency_key, has_parent):
    import datetime
    entry = json.dumps({
        "event": "kanban_create",
        "task_id": task_id,
        "assignee": assignee,
        "initial_status": initial_status,
        "has_idempotency_key": has_idempotency_key,
        "has_parent": has_parent,
        "board": KANBAN_BOARD,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    print(entry, flush=True)

def kanban_create_task(payload):
    # 1. Reject unknown fields
    unknown = set(payload.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        return _error(400, "unknown_field", offending=sorted(unknown))

    # 2. Validate title
    title_raw = payload.get("title")
    if not title_raw or not str(title_raw).strip():
        return _error(400, "title_required")
    title = _sanitise_text(title_raw).strip()
    if not title:
        return _error(400, "title_required")
    if len(title) > TITLE_MAX:
        return _error(400, "title_too_long")

    # 3. Validate body
    body_raw = payload.get("body")
    if not body_raw or not str(body_raw).strip():
        return _error(400, "body_required")
    body = _sanitise_text(body_raw).strip()
    if not body:
        return _error(400, "body_required")
    if len(body) > BODY_MAX:
        return _error(400, "body_too_long")

    # 4. Validate assignee
    assignee_raw = payload.get("assignee")
    if not assignee_raw or not str(assignee_raw).strip():
        return _error(400, "assignee_required")
    assignee = str(assignee_raw).strip()
    if assignee not in ALLOWED_ASSIGNEES:
        return _error(400, "assignee_not_allowed",
                      allowed=list(sorted(ALLOWED_ASSIGNEES)))

    # 5. Validate initial_status (ready or blocked only)
    initial_status = str(payload.get("initial_status", "ready")).strip()
    if initial_status not in ALLOWED_INITIAL_STATUSES:
        return _error(400, "invalid_initial_status",
                      allowed=list(sorted(ALLOWED_INITIAL_STATUSES)))

    # 6. Validate optional fields
    ik_result = _validate_optional_string(payload.get("idempotency_key"), IDEMPOTENCY_KEY_MAX, IDEMPOTENCY_KEY_RE, "idempotency_key")
    if isinstance(ik_result, dict):
        return ik_result
    idempotency_key = ik_result

    cb_result = _validate_optional_string(payload.get("created_by"), CREATED_BY_MAX, CREATED_BY_RE, "created_by")
    if isinstance(cb_result, dict):
        return cb_result
    created_by = cb_result

    parent_raw = payload.get("parent")
    parent = None
    if parent_raw is not None and str(parent_raw).strip():
        parent = str(parent_raw).strip()
        if not PARENT_RE.match(parent):
            return _error(400, "invalid_parent")

    priority_raw = payload.get("priority")
    priority = None
    if priority_raw is not None:
        try:
            priority = int(priority_raw)
            if priority < 0 or priority > 100:
                return _error(400, "invalid_priority")
        except (ValueError, TypeError):
            return _error(400, "invalid_priority")

    skills_raw = payload.get("skill")
    skills = None
    if skills_raw is not None:
        if not isinstance(skills_raw, list):
            return _error(400, "invalid_skill")
        skills = []
        for s in skills_raw:
            s_str = str(s).strip()
            if len(s_str) < 1 or len(s_str) > 64:
                return _error(400, "invalid_skill")
            skills.append(s_str)
        if len(skills) > 8:
            return _error(400, "invalid_skill")

    # 7. Build CLI args
    args = ["create", title, "--body", body, "--assignee", assignee, "--json"]

    if initial_status == "blocked":
        args += ["--initial-status", "blocked"]
    # ready → omit --initial-status (CLI default)

    if created_by:
        args += ["--created-by", created_by]
    else:
        args += ["--created-by", "elis-pm"]

    if idempotency_key:
        args += ["--idempotency-key", idempotency_key]
    if parent:
        args += ["--parent", parent]
    if priority is not None:
        args += ["--priority", str(priority)]
    for s in (skills or []):
        args += ["--skill", s]

    # 8. Execute via sanctioned host CLI
    res = run_hermes_kanban(args)

    # 9. Extract task_id
    task_id = extract_task_id(res["stdout"] + "\n" + res["stderr"])

    if res["returncode"] != 0 or not task_id:
        return _error(500, "kanban_cli_failed",
                      returncode=res["returncode"],
                      stderr_sanitised=_sanitise_text(res.get("stderr", ""), 500))

    # 10. Verify: re-read and confirm identity/assignee/status
    verify = run_hermes_kanban(["show", task_id, "--json"])
    if verify["returncode"] != 0:
        return _error(500, "kanban_verify_failed",
                      task_id=task_id,
                      returncode=verify["returncode"])

    task_data = {}
    try:
        parsed = json.loads(verify["stdout"])
        task_data = parsed.get("task", parsed)
    except Exception:
        return _error(500, "kanban_verify_parse_failed", task_id=task_id)

    verified_id = task_data.get("id") == task_id
    verified_assignee = task_data.get("assignee") == assignee
    verified_status = task_data.get("status") == initial_status
    verified = verified_id and verified_assignee and verified_status

    if not verified:
        return _error(500, "kanban_verify_mismatch",
                      expected={"task_id": task_id, "assignee": assignee, "status": initial_status},
                      actual={"task_id": task_data.get("id"),
                              "assignee": task_data.get("assignee"),
                              "status": task_data.get("status")})

    # 11. Log
    _log_create_event(task_id, assignee, initial_status, bool(idempotency_key), bool(parent))

    # 12. Return
    return _success(201, {
        "task_id": task_id,
        "board": KANBAN_BOARD,
        "assignee": assignee,
        "initial_status": initial_status,
        "verified_readable": True,
    })

# ---------------------------------------------------------------------------

def require_canary_task(task_id):
    if not re.fullmatch(r"t_[A-Za-z0-9]+", task_id or ""):
        return False, {"ok": False, "error": "invalid_task_id"}
    show = run_hermes_kanban(["show", task_id, "--json"])
    if show["returncode"] != 0:
        return False, {"ok": False, "error": "kanban_show_failed", "show": show}
    if CANARY_TITLE not in (show["stdout"] + show["stderr"]):
        return False, {"ok": False, "error": "task_is_not_canary", "task_id": task_id, "show": show}
    return True, show

def canary_create(payload):
    body = (
        "Controlled sandboxed ELIS PM Kanban/A2A production-readiness canary. "
        "No implementation work. No gate state. No production dispatch. "
        "Created through host bridge using sanctioned Hermes Kanban CLI only."
    )
    note = str(payload.get("note") or "").strip()
    if note:
        body += f"\\n\\nNote: {note[:500]}"

    run_id = str(payload.get("run_id") or int(time.time()))
    run_id = re.sub(r"[^A-Za-z0-9_.-]", "-", run_id)[:80]
    canary_key = f"{CANARY_KEY_PREFIX}-{run_id}"

    res = run_hermes_kanban([
        "create",
        CANARY_TITLE,
        "--body", body,
        "--assignee", "elis-pm",
        "--created-by", CANARY_AUTHOR,
        "--idempotency-key", canary_key,
        "--initial-status", "blocked",
        "--json",
    ])

    task_id = extract_task_id(res["stdout"] + "\\n" + res["stderr"])
    task_status = None
    try:
        parsed = json.loads(res["stdout"] or "{}")
        task_status = parsed.get("status")
    except Exception:
        pass

    ok = res["returncode"] == 0 and bool(task_id) and task_status != "done"
    return {
        "ok": ok,
        "operation": "kanban_canary_create",
        "task_id": task_id,
        "task_status": task_status,
        "canary_key": canary_key,
        "result": res,
    }

def canary_comment(payload):
    task_id = str(payload.get("task_id") or "").strip()
    text = str(payload.get("text") or "Sandboxed ELIS PM canary comment through host bridge using sanctioned Hermes Kanban CLI only.").strip()
    ok, proof = require_canary_task(task_id)
    if not ok:
        return proof
    res = run_hermes_kanban(["comment", task_id, text[:3000], "--author", CANARY_AUTHOR])
    return {"ok": res["returncode"] == 0, "operation": "kanban_canary_comment", "task_id": task_id, "result": res}

def canary_close(payload):
    task_id = str(payload.get("task_id") or "").strip()
    ok, proof = require_canary_task(task_id)
    if not ok:
        return proof

    comment = run_hermes_kanban([
        "comment",
        task_id,
        "Closing controlled sandboxed ELIS PM canary. This validates bridge-mediated Kanban mutation through sanctioned Hermes Kanban CLI only.",
        "--author", CANARY_AUTHOR,
    ])
    if comment["returncode"] != 0:
        return {"ok": False, "error": "comment_before_close_failed", "task_id": task_id, "comment": comment}

    meta = json.dumps({
        "canary": True,
        "bridge": "elis-kanban-a2a-bridge",
        "write_path": "hermes kanban CLI",
        "direct_db_write": False,
    })
    complete = run_hermes_kanban([
        "complete",
        task_id,
        "--result", "Controlled sandboxed ELIS PM canary passed.",
        "--summary", "Kanban canary create/comment/close path validated through host bridge and sanctioned Hermes Kanban CLI.",
        "--metadata", meta,
    ])

    show_after = run_hermes_kanban(["show", task_id, "--json"])
    status_after = None
    try:
        parsed = json.loads(show_after["stdout"] or "{}")
        status_after = (parsed.get("task") or {}).get("status")
    except Exception:
        pass

    stderr_l = (complete.get("stderr") or "").lower()
    ok = complete["returncode"] == 0 and "cannot complete" not in stderr_l and status_after == "done"

    return {
        "ok": ok,
        "operation": "kanban_canary_close",
        "task_id": task_id,
        "status_after": status_after,
        "comment": comment,
        "complete": complete,
        "show_after": show_after,
    }


A2A_CANARY_HELPER = "/opt/elis/local/kanban-a2a-bridge/a2a_canary_send.py"


def _bridge_read_json_body(handler):
    try:
        length = int(handler.headers.get("content-length") or "0")
    except Exception:
        length = 0
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8") or "{}")


def a2a_canary_send(body):
    """Controlled A2A canary wrapper.

    Calls the standalone helper, which uses the existing ELIS PM client scaffold
    and official A2A SDK path:
    PM client -> ClientFactory/SendMessageRequest -> localhost /a2a JSON-RPC.

    No Kanban mutation, no DB write, no production dispatch.
    """
    body = body or {}
    target = str(body.get("target") or "both").strip().lower()
    note = str(body.get("note") or "")[:300]

    if target not in {"advisor", "supervisor", "both"}:
        return {
            "ok": False,
            "operation": "a2a_canary_send",
            "error": "invalid_target",
            "allowed_targets": ["advisor", "supervisor", "both"],
        }

    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/elis/repo"

    proc = subprocess.run(
        ["/opt/elis/a2a/venv/bin/python", A2A_CANARY_HELPER],
        input=json.dumps({"target": target, "note": note}),
        text=True,
        capture_output=True,
        timeout=120,
        env=env,
    )

    try:
        parsed = json.loads(proc.stdout or "{}")
    except Exception:
        return {
            "ok": False,
            "operation": "a2a_canary_send",
            "error": "helper_output_parse_failed",
            "subprocess": {
                "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-2000:],
                "stderr_tail": (proc.stderr or "")[-2000:],
            },
        }

    parsed["subprocess"] = {
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-2000:],
    }
    parsed["ok"] = bool(parsed.get("ok")) and proc.returncode == 0
    return parsed

class Handler(BaseHTTPRequestHandler):
    server_version = "ELISKanbanA2ABridge/0.2"

    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args), flush=True)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return json_response(self, 200, {"ok": True, "service": "elis-kanban-a2a-bridge", "mode": "cli-wrapped-write-plus-read"})
        if path == "/kanban/identity":
            return json_response(self, 200, kanban_identity())
        if path in {"/kanban/status-counts", "/kanban/status"}:
            return json_response(self, 200, status_counts())
        if path == "/a2a/status":
            return json_response(self, 200, a2a_status())
        if path == "/a2a/registry":
            return json_response(self, 200, a2a_registry())
        if path == "/a2a/agents":
            return json_response(self, 200, a2a_agents())
        if path == "/a2a/routes":
            return json_response(self, 200, a2a_routes())
        return json_response(self, 404, {"ok": False, "error": "not_found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = read_json_body(self)
            if path in {"/a2a/canary-send", "/a2a/canary"}:
                # Do not read self.rfile here. Some do_POST flows have already
                # consumed the request body before route dispatch; a second read
                # can block until client timeout. The canary defaults to
                # target="both", so an empty body is safe for validation.
                req_body = locals().get("body")
                if req_body is None:
                    req_body = locals().get("payload")
                if req_body is None:
                    req_body = {}
                return json_response(self, 200, a2a_canary_send(req_body))

            if path == "/kanban/canary-create":
                out = canary_create(payload)
                return json_response(self, 200 if out.get("ok") else 500, out)
            if path == "/kanban/create":
                out = kanban_create_task(payload)
                status_code = out.pop("status", 201)
                return json_response(self, status_code, out)
            if path == "/kanban/canary-comment":
                out = canary_comment(payload)
                return json_response(self, 200 if out.get("ok") else 400, out)
            if path == "/kanban/canary-close":
                out = canary_close(payload)
                return json_response(self, 200 if out.get("ok") else 400, out)
            return json_response(self, 404, {"ok": False, "error": "not_found", "path": path})
        except Exception as exc:
            return json_response(self, 500, {"ok": False, "error": type(exc).__name__, "message": str(exc)})

if __name__ == "__main__":
    if not BOARD_PATH.exists():
        raise SystemExit(f"Kanban DB not found: {BOARD_PATH}")
    # Board fail-closed assertion: must be elis-core
    if KANBAN_BOARD != "elis-core":
        raise SystemExit(f"KANBAN_BOARD must be 'elis-core', got '{KANBAN_BOARD}'")
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f"ELIS Kanban/A2A bridge listening on http://{BIND_HOST}:{BIND_PORT}", flush=True)
    print(f"Board: {KANBAN_BOARD}  DB: {BOARD_PATH}", flush=True)
    server.serve_forever()
