#!/usr/bin/env python3
import asyncio
import json
import sys
from datetime import datetime, timezone

from elis.a2a.pm.client import AdvisorClient, SupervisorClient


async def run_one(label, client_obj, note):
    card = await client_obj.resolve_card()
    sdk_client = client_obj.build_client(card)

    text = (
        "PO-approved sandbox bridge A2A canary. "
        "Validate sandboxed PM bridge-to-agent acknowledgement path only. "
        "No production dispatch, no Kanban mutation, no governance-sensitive action."
    )
    if note:
        text += " Note: " + note

    responses = await client_obj.send_message(
        sdk_client,
        message_type="request",
        text=text,
        task_ref="sandboxed-elis-pm-a2a-canary",
    )

    completed = any(
        isinstance(r, dict) and r.get("state") == "TASK_STATE_COMPLETED"
        for r in responses
    )

    return {
        "label": label,
        "client": repr(client_obj),
        "card_name": getattr(card, "name", None),
        "card_version": getattr(card, "version", None),
        "response_count": len(responses) if hasattr(responses, "__len__") else None,
        "completed": completed,
        "responses": responses,
    }


async def main():
    req = json.load(sys.stdin)
    target = str(req.get("target") or "both").strip().lower()
    note = str(req.get("note") or "")[:300]

    if target not in {"advisor", "supervisor", "both"}:
        print(json.dumps({
            "ok": False,
            "operation": "a2a_canary_send",
            "error": "invalid_target",
            "allowed_targets": ["advisor", "supervisor", "both"],
        }, indent=2))
        raise SystemExit(2)

    results = []

    if target in ("advisor", "both"):
        results.append(await run_one(
            "pm_to_advisor",
            AdvisorClient(base_url="http://127.0.0.1:9500"),
            note,
        ))

    if target in ("supervisor", "both"):
        results.append(await run_one(
            "pm_to_supervisor",
            SupervisorClient(base_url="http://127.0.0.1:9501"),
            note,
        ))

    ok = bool(results) and all(r.get("completed") for r in results)

    print(json.dumps({
        "ok": ok,
        "operation": "a2a_canary_send",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "write_path": "official A2A SDK client -> localhost JSON-RPC /a2a",
        "direct_db_write": False,
        "direct_kanban_mutation": False,
        "production_dispatch": False,
        "results": results,
    }, indent=2, default=str))

    raise SystemExit(0 if ok else 1)


asyncio.run(main())
