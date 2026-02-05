#!/usr/bin/env python3
"""Read-only ledger vs exchange reconciliation report."""
import argparse
from typing import Dict

from alphagenesis.data.weex_client import WEEXClient
from alphagenesis.execution.position_ledger import PositionLedger


def _exchange_position_for(symbol: str) -> Dict:
    client = WEEXClient()
    positions = client.get_position() or []
    for pos in positions:
        if pos.get("symbol") == symbol and float(pos.get("size", 0) or 0) > 0:
            side = pos.get("side") or ""
            side = side.upper()
            if side not in ("LONG", "SHORT"):
                # fallback for numeric side values
                try:
                    side = "LONG" if int(side) == 1 else "SHORT"
                except Exception:
                    side = "UNKNOWN"
            return {
                "symbol": symbol,
                "side": side,
                "size": float(pos.get("size", 0) or 0),
            }
    return {"symbol": symbol, "side": "FLAT", "size": 0.0}


def _ledger_position_for(symbol: str) -> Dict:
    ledger = PositionLedger()
    pos = ledger.get_position(symbol)
    return {"symbol": symbol, "side": pos.side, "size": float(pos.size)}


def _classify(ledger: Dict, exchange: Dict) -> Dict:
    if ledger["side"] == "FLAT" and exchange["side"] != "FLAT":
        return {
            "mismatch": True,
            "classification": "LEDGER_MISSING",
            "suggested_action": "adopt-exchange",
        }
    if ledger["side"] != "FLAT" and exchange["side"] == "FLAT":
        return {
            "mismatch": True,
            "classification": "EXCHANGE_MISSING",
            "suggested_action": "flat-first",
        }
    if ledger["side"] != exchange["side"]:
        return {
            "mismatch": True,
            "classification": "SIDE_MISMATCH",
            "suggested_action": "adopt-exchange",
        }
    if abs(ledger["size"] - exchange["size"]) > 1e-8:
        return {
            "mismatch": True,
            "classification": "SIZE_MISMATCH",
            "suggested_action": "adopt-exchange",
        }
    return {"mismatch": False, "classification": "OK", "suggested_action": "none"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args()

    exchange = _exchange_position_for(args.symbol)
    ledger = _ledger_position_for(args.symbol)
    status = _classify(ledger, exchange)

    print(
        "symbol={symbol} exchange_side={exchange_side} exchange_size={exchange_size} "
        "ledger_side={ledger_side} ledger_size={ledger_size} mismatch={mismatch} "
        "classification={classification} suggested_action={suggested_action}".format(
            symbol=args.symbol,
            exchange_side=exchange["side"],
            exchange_size=exchange["size"],
            ledger_side=ledger["side"],
            ledger_size=ledger["size"],
            mismatch=str(status["mismatch"]).lower(),
            classification=status["classification"],
            suggested_action=status["suggested_action"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
