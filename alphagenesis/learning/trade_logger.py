"""
Trade Logger - Comprehensive audit trail for all trading activity

This module provides append-only, machine-parseable logging of every
trade action and outcome for hackathon validation and continuous improvement.

Log Format: JSONL (one JSON object per line)
Log Location: logs/trades/YYYY-MM-DD.jsonl
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class TradeLogger:
    """
    Append-only trade event logger for audit trail and analysis.

    Every significant trading event is logged:
    - Order creation
    - Order acknowledgement
    - Order fill (full or partial)
    - Position close
    - Stop loss / take profit triggers
    - Risk gate decisions
    """

    def __init__(self, base_dir: str = "logs/trades"):
        """Initialize trade logger with base directory for trade logs"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = None
        self.current_date = None
        logger.info(f"Trade logger initialized: {self.base_dir}")

    def _get_log_file(self) -> Path:
        """Get current log file path (rotates daily)"""
        today = datetime.now(timezone.utc).date().isoformat()

        if today != self.current_date:
            self.current_date = today
            self.current_file = self.base_dir / f"{today}.jsonl"
            logger.info(f"Trade log file: {self.current_file}")

        return self.current_file

    def _write_event(self, event: Dict[str, Any]):
        """Write event to log file (thread-safe append)"""
        try:
            log_file = self._get_log_file()

            # Ensure UTC timestamp
            if 'timestamp' not in event:
                event['timestamp'] = datetime.now(timezone.utc).isoformat()
            elif isinstance(event['timestamp'], (int, float)):
                # Convert Unix timestamp to ISO format
                event['timestamp'] = datetime.fromtimestamp(
                    event['timestamp'], tz=timezone.utc
                ).isoformat()

            # Write as single line JSON
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')

        except Exception as e:
            logger.error(f"Failed to write trade log: {e}")

    def log_signal_generated(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        strategy: str,
        regime: str,
        entry_price: float,
        position_size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        features: Optional[Dict] = None
    ):
        """Log when a trading signal is generated"""
        self._write_event({
            'event_type': 'signal_generated',
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'strategy': strategy,
            'regime': regime,
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'features': features or {}
        })

    def log_risk_gate_decision(
        self,
        symbol: str,
        direction: str,
        gate_type: str,
        approved: bool,
        reason: str,
        account_state: Optional[Dict] = None
    ):
        """Log risk gate decisions (ledger, gross exposure, risk manager, ethics)"""
        self._write_event({
            'event_type': 'risk_gate',
            'symbol': symbol,
            'direction': direction,
            'gate_type': gate_type,
            'approved': approved,
            'reason': reason,
            'account_state': account_state or {}
        })

    def log_order_created(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: Optional[str] = None,
        regime: Optional[str] = None
    ):
        """Log when an order is created and sent to exchange"""
        self._write_event({
            'event_type': 'order_created',
            'symbol': symbol,
            'side': side,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'strategy': strategy,
            'regime': regime
        })

    def log_order_acknowledged(
        self,
        symbol: str,
        order_id: str,
        exchange_order_id: str,
        status: str,
        response: Optional[Dict] = None
    ):
        """Log when exchange acknowledges order"""
        self._write_event({
            'event_type': 'order_acknowledged',
            'symbol': symbol,
            'order_id': order_id,
            'exchange_order_id': exchange_order_id,
            'status': status,
            'response': response or {}
        })

    def log_order_filled(
        self,
        symbol: str,
        order_id: str,
        side: str,
        quantity: float,
        fill_price: float,
        fill_type: str,  # 'full' or 'partial'
        notional_value: float,
        fees: float = 0.0
    ):
        """Log when order is filled (full or partial)"""
        self._write_event({
            'event_type': 'order_filled',
            'symbol': symbol,
            'order_id': order_id,
            'side': side,
            'quantity': quantity,
            'fill_price': fill_price,
            'fill_type': fill_type,
            'notional_value': notional_value,
            'fees': fees
        })

    def log_position_opened(
        self,
        symbol: str,
        position_id: str,
        side: str,
        quantity: float,
        entry_price: float,
        notional_value: float,
        leverage: float,
        margin_used: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ):
        """Log when position is opened"""
        self._write_event({
            'event_type': 'position_opened',
            'symbol': symbol,
            'position_id': position_id,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'notional_value': notional_value,
            'leverage': leverage,
            'margin_used': margin_used,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        })

    def log_position_closed(
        self,
        symbol: str,
        position_id: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        realized_pnl: float,
        holding_time_seconds: float,
        close_reason: str,  # 'stop_loss', 'take_profit', 'manual', 'liquidation'
        strategy: Optional[str] = None,
        regime: Optional[str] = None
    ):
        """Log when position is closed"""
        self._write_event({
            'event_type': 'position_closed',
            'symbol': symbol,
            'position_id': position_id,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'realized_pnl': realized_pnl,
            'pnl_percent': ((exit_price - entry_price) / entry_price * 100) if side == 'LONG'
                           else ((entry_price - exit_price) / entry_price * 100),
            'holding_time_seconds': holding_time_seconds,
            'holding_time_minutes': holding_time_seconds / 60,
            'close_reason': close_reason,
            'strategy': strategy,
            'regime': regime
        })

    def log_stop_loss_triggered(
        self,
        symbol: str,
        position_id: str,
        stop_loss_price: float,
        trigger_price: float,
        realized_pnl: float
    ):
        """Log when stop loss is triggered"""
        self._write_event({
            'event_type': 'stop_loss_triggered',
            'symbol': symbol,
            'position_id': position_id,
            'stop_loss_price': stop_loss_price,
            'trigger_price': trigger_price,
            'realized_pnl': realized_pnl
        })

    def log_take_profit_triggered(
        self,
        symbol: str,
        position_id: str,
        take_profit_price: float,
        trigger_price: float,
        realized_pnl: float
    ):
        """Log when take profit is triggered"""
        self._write_event({
            'event_type': 'take_profit_triggered',
            'symbol': symbol,
            'position_id': position_id,
            'take_profit_price': take_profit_price,
            'trigger_price': trigger_price,
            'realized_pnl': realized_pnl
        })

    def log_account_snapshot(
        self,
        balance: float,
        equity: float,
        unrealized_pnl: float,
        margin_used: float,
        total_notional: float,
        daily_pnl: float,
        daily_pnl_percent: float,
        open_positions: int
    ):
        """Log periodic account state snapshot"""
        self._write_event({
            'event_type': 'account_snapshot',
            'balance': balance,
            'equity': equity,
            'unrealized_pnl': unrealized_pnl,
            'margin_used': margin_used,
            'margin_used_percent': (margin_used / equity * 100) if equity > 0 else 0,
            'total_notional': total_notional,
            'gross_exposure_percent': (total_notional / equity * 100) if equity > 0 else 0,
            'daily_pnl': daily_pnl,
            'daily_pnl_percent': daily_pnl_percent * 100,
            'open_positions': open_positions
        })

    def log_daily_summary(
        self,
        date: str,
        starting_balance: float,
        ending_balance: float,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        total_pnl: float,
        total_fees: float,
        max_drawdown: float,
        strategies_used: Dict[str, int]
    ):
        """Log end-of-day summary"""
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        self._write_event({
            'event_type': 'daily_summary',
            'date': date,
            'starting_balance': starting_balance,
            'ending_balance': ending_balance,
            'pnl': ending_balance - starting_balance,
            'pnl_percent': ((ending_balance - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'max_drawdown': max_drawdown,
            'strategies_used': strategies_used
        })

    def log_error(
        self,
        error_type: str,
        error_message: str,
        symbol: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Log trading errors for debugging"""
        self._write_event({
            'event_type': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'symbol': symbol,
            'context': context or {}
        })


# Global singleton
_trade_logger = None

def get_trade_logger() -> TradeLogger:
    """Get global trade logger instance"""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLogger()
    return _trade_logger
