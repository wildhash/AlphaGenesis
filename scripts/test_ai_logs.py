#!/usr/bin/env python3
import time
from alphagenesis.omni.ai_logs.ai_log_bus import AILogBus
from alphagenesis.omni.ai_logs.ai_log_store import AILogStore


def main():
    store = AILogStore("/opt/AlphaGenesis/tmp/ai_logs.sqlite")
    bus = AILogBus(store)

    symbol = "cmt_btcusdt"
    regime = "low_volatility"
    reason = "LOW_VOL_SHORT_GATE_X3_WITH_ATR"
    confidence = 0.68
    now_ms = int(time.time() * 1000)

    bus.emit(
        stage="Strategy Evaluation",
        model="SDM:momentum",
        input_payload={
            "symbol": symbol,
            "regime": regime,
            "momentum_pct": -4.2,
            "rsi": 42.5,
            "atr": 0.35,
            "funding_rate": 0.0001,
            "current_positions": 2,
            "risk_headroom": 0.18,
        },
        output_payload={
            "direction": "SHORT",
            "confidence": confidence,
            "entry_price": 69160.9,
            "position_size": 0.002,
            "stop_loss": 69700.0,
            "take_profit": 67600.0,
        },
        explanation=(
            "Eval: regime=low_volatility, mom=-4.2, rsi=42.5, atr=0.35; "
            "chose SHORT conf=0.68 reason=LOW_VOL_SHORT_GATE_X3_WITH_ATR."
        ),
    )

    gate_results = {
        "ledger_ok": True,
        "gross_exposure_ok": True,
        "risk_ok": True,
        "min_size_floor_applied": True,
        "straddle_bypassed": True,
        "block_reason": None,
    }
    bus.emit(
        stage="Risk & Constraints",
        model="RiskManagerVeto",
        input_payload={
            "symbol": symbol,
            "side": "SHORT",
            "size": 0.002,
            "entry_price": 69160.9,
            "balance": 1565.0,
            "equity": 1565.0,
            "margin_used": 0.0,
            "gate_results": gate_results,
        },
        output_payload={
            "approved": True,
            "veto_reasons": [],
            "gate_results": gate_results,
        },
        explanation=(
            "Risk: ledger_ok=True risk_ok=True gross_ok=True; block_reason=None."
        ),
    )

    bus.emit(
        stage="Decision Making",
        model="AlphaGenesis-SDM-v1",
        input_payload={
            "symbol": symbol,
            "regime": regime,
            "signal": reason,
            "confidence": confidence,
            "momentum_pct": -4.2,
            "atr": 0.35,
            "rsi": 42.5,
            "gate_results": gate_results,
        },
        output_payload={
            "action": "SHORT",
            "position_size": 0.002,
            "risk_approved": True,
            "ledger_approved": True,
            "gross_exposure_blocked": False,
            "gate_results": gate_results,
        },
        explanation=(
            "Eval: regime=low_volatility, mom=-4.2, rsi=42.5, atr=0.35; "
            "chose SHORT conf=0.68 reason=LOW_VOL_SHORT_GATE_X3_WITH_ATR; "
            "gates ledger_ok=True risk_ok=True gross_ok=True."
        ),
    )

    bus.emit(
        stage="Order Execution",
        model="SDM:momentum",
        input_payload={
            "symbol": symbol,
            "side": "SHORT",
            "size": 0.002,
            "entry_price": 69160.9,
            "order_params": {
                "symbol": symbol,
                "side": "SHORT",
                "size": 0.002,
                "entry_price": 69160.9,
                "is_market": True,
            },
        },
        output_payload={
            "success": True,
            "order_id": f"test_order_{now_ms}",
            "code": 0,
            "msg": "success",
            "status_code": 200,
            "exchange_response": {
                "orderId": f"test_order_{now_ms}",
                "status": "success",
                "msg": "success",
            },
        },
        explanation=(
            f"Exec: size=0.002 price=69160.9; orderId=test_order_{now_ms} status=success."
        ),
    )

    print("test_ai_logs: OK")
    print("pending_ai_logs=", store.pending_count())


if __name__ == "__main__":
    main()
