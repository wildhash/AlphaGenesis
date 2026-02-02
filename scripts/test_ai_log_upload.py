#!/usr/bin/env python3
"""
Test script for WEEX AI log upload functionality.

This script tests the AI log upload without placing real orders.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenesis.data import WEEXClient
from loguru import logger


def test_ai_log_upload():
    """Test uploading a sample AI log to WEEX."""

    # Initialize WEEX client
    client = WEEXClient(
        api_key=os.getenv('WEEX_API_KEY'),
        api_secret=os.getenv('WEEX_API_SECRET'),
        api_passphrase=os.getenv('WEEX_API_PASSPHRASE')
    )

    logger.info("Testing WEEX AI log upload...")

    # Sample AI log data (mimicking real trading scenario)
    input_data = {
        "symbol": "cmt_btcusdt",
        "market_regime": "WEAK_UPTREND",
        "technical_indicators": {
            "RSI_14": 62.3,
            "EMA_20": 68950.4,
            "EMA_50": 68820.2,
            "momentum_pct": 1.2,
            "ATR": 450.0,
            "volatility": 0.0065
        },
        "current_price": 68980.5,
        "strategy_context": {
            "chosen_strategy": "momentum",
            "bandit_algorithm": "UCB (Upper Confidence Bound)",
            "exploration_rate": 0.2
        },
        "prompt": "Analyze cmt_btcusdt market data and generate trading signal for WEAK_UPTREND regime using momentum strategy with technical indicators."
    }

    output_data = {
        "signal": "LONG",
        "confidence": 0.72,
        "entry_price": 68980.5,
        "position_size": 0.015,
        "stop_loss": 67944.09,
        "take_profit": 71052.91,
        "risk_reward_ratio": 2.0,
        "reasoning": "Uptrend momentum: RSI=62.3, EMA20>68820, Mom=1.2%",
        "technical_analysis": {
            "trend": "UPTREND",
            "rsi_state": "NEUTRAL",
            "momentum": "POSITIVE"
        }
    }

    explanation = (
        "AI Analysis for cmt_btcusdt in WEAK_UPTREND regime: "
        "Technical indicators show UPTREND (EMA20 68950.40 vs EMA50 68820.20), "
        "RSI at 62.3 (neutral), momentum +1.20%. "
        "Contextual bandit (UCB algorithm) selected momentum strategy based on historical performance. "
        "AI generated LONG signal with 72.00% confidence. "
        "Risk management: stop loss at $67944.09, take profit at $71052.91. "
        "Position sizing: 0.015000 units (3% of capital for optimal learning rate)."
    )

    # Test upload (without order_id for testing)
    result = client.upload_ai_log(
        order_id=None,
        stage="Strategy Generation",
        model="AlphaGenesis-SDM-v2.0-Momentum",
        input_data=input_data,
        output_data=output_data,
        explanation=explanation
    )

    logger.info(f"Upload result: {result}")

    if result.get('code') == '00000':
        logger.info("✓ TEST PASSED: AI log uploaded successfully!")
        return True
    else:
        logger.error(f"✗ TEST FAILED: {result}")
        return False


if __name__ == "__main__":
    success = test_ai_log_upload()
    sys.exit(0 if success else 1)
