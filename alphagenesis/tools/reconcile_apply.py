#!/usr/bin/env python3
"""Apply ledger reconciliation for a single symbol (adopt exchange or set flat)."""
import argparse
import sys
from pathlib import Path
from typing import Dict

from alphagenesis.data.weex_client import WEEXClient
from alphagenesis.execution.position_ledger import PositionLedger, Position


def _exchange_position_for(symbol: str) -> Dict:
    client = WEEXClient()
    positions = client.get_position() or []
    for pos in positions:
        if pos.get("symbol") == symbol and float(pos.get("size", 0) or 0) > 0:
            side = pos.get("side") or ""
            side = side.upper()
            if side not in ("LONG", "SHORT"):
                try:
                    side = "LONG" if int(side) == 1 else "SHORT"
                except Exception:
                    side = "UNKNOWN"
            return {
                "symbol": symbol,
                "side": side,
                "size": float(pos.get("size", 0) or 0),
                "entry_price": float(pos.get("open_value", 0) or 0) / float(pos.get("size", 1) or 1),
            }
    return {"symbol": symbol, "side": "FLAT", "size": 0.0, "entry_price": 0.0}


def _backup_ledger(ledger: PositionLedger) -> Path:
    ledger_path = Path(ledger.ledger_path)
    backup = ledger_path.with_suffix(ledger_path.suffix + f".backup_{int(__import__('time').time())}")
    if ledger_path.exists():
        backup.write_bytes(ledger_path.read_bytes())
    return backup


def _ledger_position_for(ledger: PositionLedger, symbol: str) -> Dict:
    pos = ledger.get_position(symbol)
    return {"symbol": symbol, "side": pos.side, "size": float(pos.size)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--mode", choices=["adopt_exchange", "set_flat"], required=True)
    parser.add_argument("--i_understand_risk", required=True)
    args = parser.parse_args()

    if args.i_understand_risk.lower() != "true":
        print("ERROR: --i_understand_risk true is required.")
        return 2

    ledger = PositionLedger()
    exchange = _exchange_position_for(args.symbol)
    ledger_before = _ledger_position_for(ledger, args.symbol)

    backup_path = _backup_ledger(ledger)

    if args.mode == "set_flat":
        new_pos = Position(
            symbol=args.symbol,
            side="FLAT",
            size=0.0,
            entry_price=0.0,
            open_time=0.0,
            position_id=ledger.get_position(args.symbol).position_id,
        )
    else:
        if exchange["side"] not in ("LONG", "SHORT"):
            print(f"ERROR: Exchange side is {exchange['side']} for {args.symbol}, cannot adopt.")
            return 3
        new_pos = Position(
            symbol=args.symbol,
            side=exchange["side"],
            size=float(exchange["size"]),
            entry_price=float(exchange.get("entry_price", 0.0)),
            open_time=__import__('time').time(),
            position_id=ledger.get_position(args.symbol).position_id,
        )

    ledger.positions[args.symbol] = new_pos
    ledger.desync_events.pop(args.symbol, None)
    ledger._save(force=True)

    ledger_after = _ledger_position_for(ledger, args.symbol)

    mismatch_before = ledger_before["side"] != exchange["side"] or abs(ledger_before["size"] - exchange["size"]) > 1e-8
    mismatch_after = ledger_after["side"] != exchange["side"] or abs(ledger_after["size"] - exchange["size"]) > 1e-8

    print(f"backup_path={backup_path}")
    print(
        "symbol={symbol} exchange_side={exchange_side} exchange_size={exchange_size} "
        "ledger_before_side={ledger_before_side} ledger_before_size={ledger_before_size} "
        "ledger_after_side={ledger_after_side} ledger_after_size={ledger_after_size} "
        "mismatch_before={mismatch_before} mismatch_after={mismatch_after}".format(
            symbol=args.symbol,
            exchange_side=exchange["side"],
            exchange_size=exchange["size"],
            ledger_before_side=ledger_before["side"],
            ledger_before_size=ledger_before["size"],
            ledger_after_side=ledger_after["side"],
            ledger_after_size=ledger_after["size"],
            mismatch_before=str(mismatch_before).lower(),
            mismatch_after=str(mismatch_after).lower(),
        )
    )

    print("NEXT: python3 -m alphagenesis.tools.reconcile_report --symbol {0}".format(args.symbol))
    print("NEXT: sudo systemctl start sdm-trading.service")
    print("NEXT: sudo journalctl -u sdm-trading.service --since '2 minutes ago' --no-pager | grep -E 'SAFE MODE|LEDGER MISMATCH|RECONCILE|STRADDLE|TIME STOP|BREAKOUT|HEDGED|RUNNER|TRAILING' | tail -80")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
