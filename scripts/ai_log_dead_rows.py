#!/usr/bin/env python3
"""Inspect and optionally requeue dead AI-log rows."""

import argparse
import json
import sqlite3
import time
from typing import List, Tuple

TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "tempor",
    "connection",
    "network",
    "429",
    "500",
    "502",
    "503",
    "504",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect/requeue dead ai_logs rows")
    parser.add_argument("--db", default="/opt/AlphaGenesis/tmp/ai_logs.sqlite", help="Path to ai_logs sqlite")
    parser.add_argument("--limit", type=int, default=20, help="How many dead rows to inspect")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--requeue-transient", action="store_true", help="Set transient dead rows back to retry")
    mode.add_argument(
        "--mark-terminal",
        action="store_true",
        help="Mark permanent dead rows as terminal-complete (keeps row evidence, removes dead backlog)",
    )
    parser.add_argument(
        "--terminal-marker",
        default="permanent_40753",
        help="Substring marker in last_error used to detect terminal rows",
    )
    parser.add_argument(
        "--terminal-status",
        default="done",
        help="Status to set for terminal rows (default: done)",
    )
    parser.add_argument(
        "--terminal-reason",
        default="terminal_marked_by_script",
        help="Prefix stored in last_error when marking terminal rows",
    )
    return parser.parse_args()


def is_transient(error: str) -> bool:
    e = (error or "").lower()
    return any(marker in e for marker in TRANSIENT_MARKERS)


def main() -> int:
    args = parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT id, created_at_ms, stage, model, attempts, last_error, payload_json
        FROM ai_logs
        WHERE status='dead'
        ORDER BY created_at_ms DESC
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()

    if not rows:
        print("No dead rows found.")
        return 0

    transient_ids: List[str] = []
    terminal_ids: List[str] = []
    terminal_payloads: List[Tuple[str, str]] = []
    marker = (args.terminal_marker or "").lower().strip()

    print(f"Dead rows found: {len(rows)}")
    for row in rows:
        payload = {}
        try:
            payload = json.loads(row["payload_json"])
        except Exception:
            payload = {}
        inp = payload.get("input", {}) if isinstance(payload, dict) else {}
        symbol = inp.get("symbol")
        reason = inp.get("entry_reason") or inp.get("signal") or inp.get("reason")
        err = row["last_error"] or ""
        transient = is_transient(err)
        if transient:
            transient_ids.append(row["id"])
        is_terminal = bool(marker) and (marker in err.lower()) and not transient
        if is_terminal:
            terminal_ids.append(row["id"])
            terminal_payloads.append(
                (
                    f"{args.terminal_reason}|{(err or '')[:900]}",
                    row["id"],
                )
            )

        print(
            "id={id} stage={stage} model={model} attempts={attempts} symbol={symbol} reason={reason} transient={transient} terminal_match={terminal}".format(
                id=row["id"],
                stage=row["stage"],
                model=row["model"],
                attempts=row["attempts"],
                symbol=symbol,
                reason=reason,
                transient=transient,
                terminal=is_terminal,
            )
        )
        print(f"  last_error={err[:220]}")

    if args.requeue_transient and transient_ids:
        next_attempt_ms = int(time.time() * 1000) + 1000
        with conn:
            conn.executemany(
                """
                UPDATE ai_logs
                SET status='retry', next_attempt_at_ms=?, last_error=?
                WHERE id=?
                """,
                [
                    (next_attempt_ms, "requeued_transient_by_script", event_id)
                    for event_id in transient_ids
                ],
            )
        print(f"Requeued transient dead rows: {len(transient_ids)}")
    elif args.requeue_transient:
        print("No transient dead rows matched for requeue.")

    if args.mark_terminal and terminal_ids:
        with conn:
            conn.executemany(
                """
                UPDATE ai_logs
                SET status=?, next_attempt_at_ms=0, last_error=?
                WHERE id=?
                """,
                [
                    (args.terminal_status, last_error, event_id)
                    for (last_error, event_id) in terminal_payloads
                ],
            )
        print(
            "Terminal-marked rows: {count} (status={status}, marker={marker})".format(
                count=len(terminal_ids),
                status=args.terminal_status,
                marker=args.terminal_marker,
            )
        )
    elif args.mark_terminal:
        print(f"No dead rows matched terminal marker '{args.terminal_marker}'.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
