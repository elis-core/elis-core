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
        if path == "/kanban/status-counts":
            return json_response(self, 200, status_counts())
        if path == "/a2a/status":
            return json_response(self, 200, a2a_status())
        return json_response(self, 404, {"ok": False, "error": "not_found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = read_json_body(self)
            if path == "/a2a/canary-send":
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
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f"ELIS Kanban/A2A bridge listening on http://{BIND_HOST}:{BIND_PORT}", flush=True)
    server.serve_forever()
