#!/usr/bin/env python3
"""Summarize recent trading edge from AI logs and journald exits."""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate edge report from AI logs")
    parser.add_argument("--hours", type=int, default=4, help="Lookback window in hours")
    parser.add_argument("--db", default="/opt/AlphaGenesis/tmp/ai_logs.sqlite", help="Path to ai_logs sqlite")
    parser.add_argument("--ledger", default="/opt/AlphaGenesis/tmp/position_ledger.json", help="Path to position ledger json")
    parser.add_argument("--service", default="sdm-trading.service", help="systemd service name")
    parser.add_argument("--min-abs-pnl", type=float, default=0.001, help="Filter near-zero PnL exits (after fees)")
    parser.add_argument("--include-flat", action="store_true", help="Include exchange_flat_detected exits")
    return parser.parse_args()


def to_ts_ms(dt_text: str) -> Optional[int]:
    # Expected prefix from loguru in journalctl -o cat: "YYYY-MM-DD HH:MM:SS"
    try:
        dt = datetime.strptime(dt_text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def normalize_reason(value: Optional[str]) -> str:
    if value is None:
        return "None"
    value_s = str(value).strip()
    return value_s if value_s else "None"


def is_unattributed_exchange_close(exit_reason: str, entry_reason: str, regime: str) -> bool:
    exit_reason_norm = str(exit_reason or "").strip().lower()
    entry_reason_norm = normalize_reason(entry_reason).strip().lower()
    regime_norm = str(regime or "").strip().lower()
    if not regime_norm:
        regime_norm = "unknown"
    if exit_reason_norm != "exchange_closed":
        return False
    return entry_reason_norm in {"none", "legacy_none", "unknown"} and regime_norm in {"none", "unknown"}


def load_ledger_exits(ledger_path: str, since_ms: int, include_flat: bool, min_abs_pnl: float) -> tuple[List[Dict[str, object]], Dict[str, object]]:
    try:
        with open(ledger_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return [], {"rows_total": 0, "rows_in_window": 0, "excluded_flat": 0, "excluded_near_zero": 0, "excluded_exchange_closed_unknown": 0}

    if isinstance(data, dict):
        rows = data.get("closed_trades", [])
    elif isinstance(data, list):
        rows = data
    else:
        rows = []

    trades: List[Dict[str, object]] = []
    excluded_flat = 0
    excluded_near_zero = 0
    excluded_exchange_closed_unknown = 0
    rows_in_window = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        close_time = row.get("close_time")
        if close_time is None:
            continue
        try:
            ts_ms = int(float(close_time) * 1000)
        except (TypeError, ValueError):
            continue
        if ts_ms < since_ms:
            continue
        rows_in_window += 1

        pnl = row.get("realized_pnl")
        if pnl is None:
            continue
        try:
            pnl_float = float(pnl)
        except (TypeError, ValueError):
            continue
        try:
            fees_float = float(row.get("fees_estimated", 0.0) or 0.0)
        except (TypeError, ValueError):
            fees_float = 0.0
        pnl_is_net = bool(row.get("pnl_is_net", False))
        if not pnl_is_net:
            pnl_float -= fees_float

        entry_reason = normalize_reason(row.get("entry_reason"))
        regime = str(row.get("entry_regime") or "unknown").strip().lower() or "unknown"
        exit_reason = str(row.get("close_reason") or "UNKNOWN")
        if is_unattributed_exchange_close(exit_reason, entry_reason, regime):
            excluded_exchange_closed_unknown += 1
            continue
        if not include_flat and exit_reason.strip().lower() == "exchange_flat_detected":
            excluded_flat += 1
            continue
        if min_abs_pnl and abs(pnl_float) < float(min_abs_pnl):
            excluded_near_zero += 1
            continue

        trades.append(
            {
                "ts_ms": ts_ms,
                "symbol": str(row.get("symbol") or "unknown").lower(),
                "entry_reason": entry_reason,
                "exit_reason": exit_reason,
                "regime": regime,
                "pnl": pnl_float,
            }
        )
    meta = {
        "rows_total": len(rows),
        "rows_in_window": rows_in_window,
        "excluded_flat": excluded_flat,
        "excluded_near_zero": excluded_near_zero,
        "excluded_exchange_closed_unknown": excluded_exchange_closed_unknown,
    }
    return trades, meta


def load_contexts(conn: sqlite3.Connection, since_ms: int) -> Tuple[Dict[Tuple[str, str], List[Tuple[int, str]]], Dict[str, List[Tuple[int, str]]]]:
    by_key: Dict[Tuple[str, str], List[Tuple[int, str]]] = defaultdict(list)
    by_symbol: Dict[str, List[Tuple[int, str]]] = defaultdict(list)

    query = """
        SELECT created_at_ms, stage, payload_json
        FROM ai_logs
        WHERE status='done'
          AND stage IN ('Strategy Evaluation', 'Decision Making')
          AND created_at_ms >= ?
        ORDER BY created_at_ms ASC
    """
    for created_at_ms, stage, payload_json in conn.execute(query, (since_ms,)):
        try:
            payload = json.loads(payload_json)
        except Exception:
            continue
        inp = payload.get("input", {}) if isinstance(payload, dict) else {}
        out = payload.get("output", {}) if isinstance(payload, dict) else {}
        symbol = str(inp.get("symbol") or "").lower().strip()
        if not symbol:
            continue

        regime = str(inp.get("regime") or "unknown")
        reason = normalize_reason(inp.get("entry_reason") or inp.get("signal") or inp.get("reason"))

        # Ignore explicit HOLD-only decision rows for mapping context.
        if stage == "Decision Making":
            action = str(out.get("action") or "").upper()
            if action == "HOLD":
                continue

        by_key[(symbol, reason)].append((int(created_at_ms), regime))
        by_symbol[symbol].append((int(created_at_ms), regime))

    return by_key, by_symbol


def resolve_regime(
    symbol: str,
    reason: str,
    ts_ms: Optional[int],
    by_key: Dict[Tuple[str, str], List[Tuple[int, str]]],
    by_symbol: Dict[str, List[Tuple[int, str]]],
) -> str:
    symbol = symbol.lower()
    reason = normalize_reason(reason)
    if ts_ms is None:
        ts_ms = int(time.time() * 1000)

    candidates = by_key.get((symbol, reason), [])
    chosen = None
    for c_ts, c_regime in candidates:
        if c_ts <= ts_ms:
            chosen = c_regime
        else:
            break
    if chosen:
        return chosen

    candidates = by_symbol.get(symbol, [])
    chosen = None
    for c_ts, c_regime in candidates:
        if c_ts <= ts_ms:
            chosen = c_regime
        else:
            break
    return chosen or "unknown"


def parse_ai_exit_logs(hours: int, service: str) -> List[Dict[str, object]]:
    cmd = [
        "journalctl",
        "-u",
        service,
        "-o",
        "cat",
        "--since",
        f"{hours} hours ago",
        "--no-pager",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception:
        return []

    if res.returncode != 0:
        return []

    trades: List[Dict[str, object]] = []
    seen = set()

    for raw_line in res.stdout.splitlines():
        if "AI_EXIT_LOG symbol=" not in raw_line:
            continue

        # Prefix timestamp is emitted by loguru in message body.
        ts_ms = None
        ts_match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", raw_line)
        if ts_match:
            ts_ms = to_ts_ms(ts_match.group(1))

        symbol_match = re.search(r"symbol=([^\s]+)", raw_line)
        exit_reason_match = re.search(r"exit_reason=([^\s]+)", raw_line)
        symbol = symbol_match.group(1).strip().lower() if symbol_match else "unknown"
        exit_reason = exit_reason_match.group(1).strip() if exit_reason_match else "UNKNOWN"

        payload_idx = raw_line.find("payload=")
        if payload_idx < 0:
            continue

        payload_raw = raw_line[payload_idx + len("payload="):].strip()
        try:
            payload = json.loads(payload_raw)
        except Exception:
            continue

        pnl = payload.get("realized_pnl")
        if pnl is None:
            continue
        try:
            pnl = float(pnl)
        except Exception:
            continue

        entry_reason = normalize_reason(payload.get("entry_reason"))

        entry_order_ids = tuple(
            str(x.get("order_id") or x.get("client_oid") or "")
            for x in payload.get("entry_order_ids", [])
            if isinstance(x, dict)
        )
        if entry_order_ids:
            dedupe_key = (symbol, exit_reason, entry_reason, entry_order_ids, round(pnl, 8))
        else:
            ts_bucket = int((ts_ms or 0) / 1000)
            dedupe_key = (symbol, exit_reason, entry_reason, ts_bucket, round(pnl, 8))

        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        trades.append(
            {
                "ts_ms": ts_ms,
                "symbol": symbol,
                "entry_reason": entry_reason,
                "exit_reason": exit_reason,
                "pnl": pnl,
            }
        )

    return trades


def fallback_sqlite_exits(conn: sqlite3.Connection, since_ms: int) -> List[Dict[str, object]]:
    trades: List[Dict[str, object]] = []
    query = """
        SELECT created_at_ms, payload_json
        FROM ai_logs
        WHERE status='done'
          AND stage='Exit Execution'
          AND created_at_ms >= ?
        ORDER BY created_at_ms ASC
    """
    for created_at_ms, payload_json in conn.execute(query, (since_ms,)):
        try:
            payload = json.loads(payload_json)
        except Exception:
            continue
        inp = payload.get("input", {}) if isinstance(payload, dict) else {}
        out = payload.get("output", {}) if isinstance(payload, dict) else {}
        pnl = out.get("realized_pnl")
        if pnl is None:
            pnl = inp.get("realized_pnl")
        if pnl is None:
            continue
        try:
            pnl = float(pnl)
        except Exception:
            continue
        trades.append(
            {
                "ts_ms": int(created_at_ms),
                "symbol": str(inp.get("symbol") or "unknown").lower(),
                "entry_reason": normalize_reason(inp.get("entry_reason")),
                "exit_reason": str(inp.get("exit_reason") or out.get("exit_reason") or "UNKNOWN"),
                "pnl": pnl,
            }
        )
    return trades


def fmt_num(value: float) -> str:
    return f"{value:,.4f}"


def main() -> int:
    args = parse_args()
    now_ms = int(time.time() * 1000)
    since_ms = now_ms - int(args.hours * 3600 * 1000)

    conn = None
    by_key: Dict[Tuple[str, str], List[Tuple[int, str]]] = defaultdict(list)
    by_symbol: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
    try:
        conn = sqlite3.connect(args.db)
        by_key, by_symbol = load_contexts(conn, since_ms)
    except sqlite3.Error:
        conn = None

    source = "ledger"
    trades, ledger_meta = load_ledger_exits(args.ledger, since_ms, include_flat=args.include_flat, min_abs_pnl=args.min_abs_pnl)
    if not trades:
        source = "sqlite"
        if conn is not None:
            try:
                trades = fallback_sqlite_exits(conn, since_ms)
            except sqlite3.Error:
                trades = []
        if not trades:
            trades = parse_ai_exit_logs(args.hours, args.service)
            source = "journalctl-fallback"
    if conn is not None:
        conn.close()

    excluded_flat_generic = 0
    excluded_near_zero_generic = 0
    excluded_exchange_closed_unknown_generic = 0
    filtered_trades: List[Dict[str, object]] = []
    for trade in trades:
        exit_reason = str(trade.get("exit_reason") or "UNKNOWN").strip().lower()
        entry_reason = normalize_reason(str(trade.get("entry_reason") or "None"))
        regime = str(trade.get("regime") or "unknown").strip().lower() or "unknown"
        pnl_val = trade.get("pnl")
        try:
            pnl_float = float(pnl_val)
        except (TypeError, ValueError):
            continue
        if is_unattributed_exchange_close(exit_reason, entry_reason, regime):
            excluded_exchange_closed_unknown_generic += 1
            continue
        if not args.include_flat and exit_reason == "exchange_flat_detected":
            excluded_flat_generic += 1
            continue
        if args.min_abs_pnl and abs(pnl_float) < args.min_abs_pnl:
            excluded_near_zero_generic += 1
            continue
        trade["pnl"] = pnl_float
        trade["entry_reason"] = entry_reason
        trade["regime"] = regime
        filtered_trades.append(trade)
    trades = filtered_trades

    total_excluded_flat = int(ledger_meta.get("excluded_flat", 0)) + excluded_flat_generic
    total_excluded_near_zero = int(ledger_meta.get("excluded_near_zero", 0)) + excluded_near_zero_generic
    total_excluded_exchange_closed_unknown = int(ledger_meta.get("excluded_exchange_closed_unknown", 0)) + excluded_exchange_closed_unknown_generic
    total_rows_in_window = int(ledger_meta.get("rows_in_window", 0))
    if ledger_meta.get("rows_in_window", 0) > 0:
        print(
            "FILTER: excluded_flat={} excluded_near_zero={} excluded_exchange_closed_unknown={} eps={} include_flat={} (ledger_rows_in_window={})".format(
                total_excluded_flat,
                total_excluded_near_zero,
                total_excluded_exchange_closed_unknown,
                args.min_abs_pnl,
                bool(args.include_flat),
                total_rows_in_window,
            )
        )
    elif total_excluded_flat > 0 or total_excluded_near_zero > 0 or total_excluded_exchange_closed_unknown > 0:
        print(
            "FILTER: excluded_flat={} excluded_near_zero={} excluded_exchange_closed_unknown={} eps={} include_flat={}".format(
                total_excluded_flat,
                total_excluded_near_zero,
                total_excluded_exchange_closed_unknown,
                args.min_abs_pnl,
                bool(args.include_flat),
            )
        )

    for trade in trades:
        regime_val = str(trade.get("regime") or "unknown").strip().lower()
        if regime_val in {"", "unknown", "none"}:
            trade["regime"] = resolve_regime(
                symbol=str(trade["symbol"]),
                reason=str(trade["entry_reason"]),
                ts_ms=trade.get("ts_ms"),
                by_key=by_key,
                by_symbol=by_symbol,
            )
        else:
            trade["regime"] = regime_val

    print(f"=== EDGE REPORT ({args.hours}h) source={source} ===")
    if not trades:
        print("No exits with realized PnL found in this window.")
        return 0

    pnl_by_reason: Dict[str, float] = defaultdict(float)
    count_by_reason: Dict[str, int] = defaultdict(int)
    pnl_by_symbol: Dict[str, float] = defaultdict(float)
    count_by_symbol: Dict[str, int] = defaultdict(int)
    exit_counts: Dict[str, int] = defaultdict(int)

    tuple_stats: Dict[Tuple[str, str, str], Dict[str, float]] = {}

    for trade in trades:
        symbol = str(trade["symbol"])
        reason = normalize_reason(str(trade["entry_reason"]))
        regime = str(trade.get("regime") or "unknown")
        pnl = float(trade["pnl"])
        exit_reason = str(trade["exit_reason"])

        pnl_by_reason[reason] += pnl
        count_by_reason[reason] += 1
        pnl_by_symbol[symbol] += pnl
        count_by_symbol[symbol] += 1
        exit_counts[exit_reason] += 1

        key = (symbol, reason, regime)
        if key not in tuple_stats:
            tuple_stats[key] = {
                "n": 0,
                "wins": 0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "total_pnl": 0.0,
            }
        st = tuple_stats[key]
        st["n"] += 1
        st["total_pnl"] += pnl
        if pnl > 0:
            st["wins"] += 1
            st["gross_profit"] += pnl
        elif pnl < 0:
            st["gross_loss"] += abs(pnl)

    total_pnl = sum(float(t["pnl"]) for t in trades)
    print(f"Exits: {len(trades)}")
    print(f"Total Realized PnL: {fmt_num(total_pnl)}")
    print()

    print("1) PnL by entry_reason")
    for reason, pnl in sorted(pnl_by_reason.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason:35s} pnl={fmt_num(pnl):>12s}  n={count_by_reason[reason]}")
    print()

    print("2) PnL by symbol")
    for symbol, pnl in sorted(pnl_by_symbol.items(), key=lambda x: x[1], reverse=True):
        print(f"  {symbol:15s} pnl={fmt_num(pnl):>12s}  n={count_by_symbol[symbol]}")
    print()

    print("3) Exit reason counts")
    for reason, cnt in sorted(exit_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason:30s} n={cnt}")
    print()

    print("4) Edge tuples (symbol, entry_reason, regime)")
    tuple_rows = []
    for (symbol, reason, regime), st in tuple_stats.items():
        n = int(st["n"])
        wins = int(st["wins"])
        win_rate = (wins / n) if n else 0.0
        gross_profit = float(st["gross_profit"])
        gross_loss = float(st["gross_loss"])
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = 999.0
        else:
            profit_factor = 0.0
        total = float(st["total_pnl"])
        tuple_rows.append((symbol, reason, regime, n, win_rate, profit_factor, total))

    for row in sorted(tuple_rows, key=lambda x: x[6], reverse=True):
        symbol, reason, regime, n, win_rate, profit_factor, total = row
        print(
            f"  {symbol:15s} | {reason:30s} | {regime:16s} | "
            f"n={n:2d} wr={win_rate:5.1%} pf={profit_factor:5.2f} pnl={fmt_num(total)}"
        )
    print()

    candidates = [
        r for r in tuple_rows
        if r[3] >= 5 and (r[4] > 0.55 or r[5] > 1.5)
    ]
    if candidates:
        best = sorted(candidates, key=lambda x: x[6], reverse=True)[0]
        print("CHAMPION_TUPLE: EDGE FOUND")
        print(
            "  symbol={} reason={} regime={} n={} win_rate={:.1%} profit_factor={:.2f} total_pnl={}".format(
                best[0], best[1], best[2], best[3], best[4], best[5], fmt_num(best[6])
            )
        )
    else:
        print("CHAMPION_TUPLE: NONE (n>=5 and win_rate>55% or PF>1.5 not met)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
