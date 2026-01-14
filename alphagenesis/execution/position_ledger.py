"""
Position Ledger - Single Source of Truth for Position Management
Prevents conflicting positions (LONG + SHORT on same symbol)
"""
import json
import time
from datetime import datetime
from typing import Dict, Optional, Literal
from pathlib import Path
from loguru import logger
from dataclasses import dataclass, asdict


PositionSide = Literal['FLAT', 'LONG', 'SHORT']


@dataclass
class Position:
    """Single position record."""
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    open_time: float  # Unix timestamp
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_update_ts: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class PositionLedger:
    """
    SINGLE SOURCE OF TRUTH for all position state.

    CRITICAL RULES:
    1. Only ONE net position per symbol (LONG, SHORT, or FLAT)
    2. Cannot open opposite side while position exists
    3. Persisted to disk for restart safety
    4. Must be confirmed against exchange before allowing new trades
    """

    def __init__(self, ledger_path: str = "/tmp/position_ledger.json"):
        self.ledger_path = Path(ledger_path)
        self.positions: Dict[str, Position] = {}
        self.cooldown_until: Dict[str, float] = {}  # symbol -> unix timestamp
        self.trades_today: Dict[str, int] = {}  # symbol -> count

        # Config
        self.cooldown_seconds = 180  # 3 minutes after close
        self.max_trades_per_day = 50  # Per symbol

        self._load()
        logger.info(f"PositionLedger initialized with {len(self.positions)} positions")

    def _load(self):
        """Load ledger from disk."""
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, 'r') as f:
                    data = json.load(f)
                    self.positions = {
                        symbol: Position.from_dict(pos_data)
                        for symbol, pos_data in data.get('positions', {}).items()
                    }
                    self.cooldown_until = data.get('cooldown_until', {})
                    self.trades_today = data.get('trades_today', {})
                logger.info(f"Loaded ledger from {self.ledger_path}")
            except Exception as e:
                logger.error(f"Failed to load ledger: {e}")
                self.positions = {}

    def _save(self):
        """Persist ledger to disk."""
        try:
            data = {
                'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
                'cooldown_until': self.cooldown_until,
                'trades_today': self.trades_today,
                'last_save': time.time()
            }
            with open(self.ledger_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

    def get_position(self, symbol: str) -> Position:
        """Get current position for symbol. Returns FLAT if none exists."""
        return self.positions.get(symbol, Position(
            symbol=symbol,
            side='FLAT',
            size=0.0,
            entry_price=0.0,
            open_time=0.0
        ))

    def can_open_position(self, symbol: str, side: Literal['LONG', 'SHORT']) -> tuple[bool, str]:
        """
        CRITICAL CONFLICT CHECK.

        Returns (can_open, reason)
        """
        current = self.get_position(symbol)
        now = time.time()

        # 1. Check cooldown
        if symbol in self.cooldown_until:
            cooldown_end = self.cooldown_until[symbol]
            if now < cooldown_end:
                remaining = int(cooldown_end - now)
                return False, f"Cooldown active: {remaining}s remaining"

        # 2. Check max trades per day
        if self.trades_today.get(symbol, 0) >= self.max_trades_per_day:
            return False, f"Max trades/day ({self.max_trades_per_day}) reached"

        # 3. CRITICAL: Check for opposite position
        if current.side == 'LONG' and side == 'SHORT':
            return False, f"❌ CONFLICT: Cannot SHORT while LONG position exists (size: {current.size})"

        if current.side == 'SHORT' and side == 'LONG':
            return False, f"❌ CONFLICT: Cannot LONG while SHORT position exists (size: {current.size})"

        # 4. Check if position already exists same side (scaling)
        if current.side == side and current.size > 0:
            return False, f"Position already exists: {side} {current.size}"

        return True, "OK"

    def open_position(self, symbol: str, side: Literal['LONG', 'SHORT'],
                     size: float, entry_price: float) -> bool:
        """
        Open new position. Returns True if successful.
        """
        can_open, reason = self.can_open_position(symbol, side)

        if not can_open:
            logger.warning(f"Cannot open {side} on {symbol}: {reason}")
            return False

        # Create position
        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            open_time=time.time(),
            last_update_ts=time.time()
        )

        # Increment trade count
        self.trades_today[symbol] = self.trades_today.get(symbol, 0) + 1

        # Clear cooldown if any
        self.cooldown_until.pop(symbol, None)

        self._save()
        logger.info(f"✅ Opened {side} position on {symbol}: size={size}, price={entry_price}")
        return True

    def close_position(self, symbol: str, close_price: float, realized_pnl: float):
        """
        Close position and start cooldown.
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot close {symbol}: no position exists")
            return

        pos = self.positions[symbol]

        # Log closure
        holding_time = time.time() - pos.open_time
        logger.info(f"✅ Closed {pos.side} position on {symbol}: "
                   f"entry={pos.entry_price:.2f}, close={close_price:.2f}, "
                   f"P&L=${realized_pnl:.2f}, holding={holding_time/60:.1f}min")

        # Set to FLAT
        self.positions[symbol] = Position(
            symbol=symbol,
            side='FLAT',
            size=0.0,
            entry_price=0.0,
            open_time=0.0,
            realized_pnl=realized_pnl,
            last_update_ts=time.time()
        )

        # Start cooldown
        self.cooldown_until[symbol] = time.time() + self.cooldown_seconds

        self._save()

    def update_unrealized_pnl(self, symbol: str, current_price: float):
        """Update unrealized P&L for open position."""
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        if pos.side == 'FLAT':
            return

        if pos.side == 'LONG':
            pos.unrealized_pnl = (current_price - pos.entry_price) * pos.size
        else:  # SHORT
            pos.unrealized_pnl = (pos.entry_price - current_price) * pos.size

        pos.last_update_ts = time.time()
        self._save()

    def reconcile_with_exchange(self, exchange_positions: list) -> bool:
        """
        Reconcile ledger with exchange state.

        Returns True if consistent, False if mismatch detected.
        """
        logger.info("Reconciling position ledger with exchange...")

        mismatches = []

        for pos_data in exchange_positions:
            symbol = pos_data['symbol']
            exchange_side = pos_data['side']  # 'LONG' or 'SHORT'
            exchange_size = float(pos_data['size'])

            ledger_pos = self.get_position(symbol)

            # Check for mismatch
            if ledger_pos.side != exchange_side:
                mismatches.append(f"{symbol}: ledger={ledger_pos.side}, exchange={exchange_side}")

            if abs(ledger_pos.size - exchange_size) > 0.001:
                mismatches.append(f"{symbol}: ledger size={ledger_pos.size}, exchange size={exchange_size}")

        if mismatches:
            logger.error(f"❌ LEDGER MISMATCH DETECTED: {mismatches}")
            logger.error("ENTERING SAFE MODE - halting new trades until manual reconciliation")
            return False

        logger.info("✅ Ledger reconciliation successful")
        return True

    def get_all_positions(self) -> Dict[str, Position]:
        """Get all non-FLAT positions."""
        return {
            symbol: pos for symbol, pos in self.positions.items()
            if pos.side != 'FLAT'
        }

    def reset_daily_counters(self):
        """Reset daily trade counters (call at UTC midnight)."""
        self.trades_today = {}
        self._save()
        logger.info("Daily trade counters reset")
