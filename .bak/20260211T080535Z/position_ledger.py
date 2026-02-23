"""
Position Ledger - Single Source of Truth for Position Management
Prevents conflicting positions (LONG + SHORT on same symbol)

PHASE 2 IMPROVEMENTS:
- Bidirectional reconciliation (ledger→exchange AND exchange→ledger)
- Auto-close detection when exchange shows flat
- Grace period for desyncs (not instant SAFE MODE)
- Atomic + throttled saves
- Auto daily counter reset
- Position IDs for idempotency
- Closed trades event log
"""
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Literal, List
from pathlib import Path
from loguru import logger
from dataclasses import dataclass, asdict, field


PositionSide = Literal['FLAT', 'LONG', 'SHORT']


@dataclass
class Position:
    """Single position record."""
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    open_time: float  # Unix timestamp
    position_id: str  # UUID for idempotency
    client_order_id: Optional[str] = None
    order_id: Optional[str] = None
    entry_reason: Optional[str] = None
    entry_regime: Optional[str] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_update_ts: float = 0.0
    last_exchange_sync_ts: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class ClosedTrade:
    """Record of closed trade for learning."""
    position_id: str
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    close_price: float
    open_time: float
    close_time: float
    holding_seconds: float
    realized_pnl: float
    close_reason: str  # 'manual', 'sl_hit', 'tp_hit', 'exchange_flat_detected', 'liquidation'
    entry_reason: str = "unknown"
    entry_regime: str = "unknown"
    fees_estimated: float = 0.0
    pnl_is_net: bool = False
    mae: float = 0.0  # Max Adverse Excursion
    mfe: float = 0.0  # Max Favorable Excursion

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DesyncEvent:
    """Track desync events for grace period."""
    symbol: str
    first_seen_ts: float
    mismatch_type: str  # 'LEDGER_MISSING', 'EXCHANGE_MISSING', 'SIDE_MISMATCH', 'SIZE_MISMATCH'
    details: str


class PositionLedger:
    """
    SINGLE SOURCE OF TRUTH for all position state.

    CRITICAL RULES:
    1. Only ONE net position per symbol (LONG, SHORT, or FLAT)
    2. Cannot open opposite side while position exists
    3. Exchange is ultimate truth - ledger syncs to exchange
    4. Bidirectional reconciliation with grace period
    5. Auto-closes positions when exchange shows flat
    6. Persisted atomically with throttling
    """

    def __init__(self, ledger_path: str = "/tmp/position_ledger.json"):
        self.ledger_path = Path(ledger_path)
        self.positions: Dict[str, Position] = {}
        self.cooldown_until: Dict[str, float] = {}  # symbol -> unix timestamp
        self.trades_today: Dict[str, int] = {}  # symbol -> count
        self.closed_trades: List[ClosedTrade] = []  # Learning dataset
        self.desync_events: Dict[str, DesyncEvent] = {}  # symbol -> desync

        # Config
        self.cooldown_seconds = 180  # 3 minutes after close
        self.max_trades_per_day = 20  # Per symbol (reduced from 50 - fee control)
        self.desync_grace_seconds = 30  # Wait 30s before SAFE MODE
        self.save_interval_seconds = 5  # Throttle saves
        self.max_closed_trades = 1000  # Keep last N for learning

        # State
        self.last_save_ts = 0.0
        self.last_counter_date = ""  # UTC date string for auto-reset

        self._load()
        self._auto_reset_daily_counters()
        logger.info(f"PositionLedger initialized with {len([p for p in self.positions.values() if p.side != 'FLAT'])} open positions")

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
                    self.last_counter_date = data.get('last_counter_date', '')

                    # Load closed trades
                    closed_data = data.get('closed_trades', [])
                    self.closed_trades = [ClosedTrade(**ct) for ct in closed_data[-self.max_closed_trades:]]

                logger.info(f"Loaded ledger from {self.ledger_path}")
            except Exception as e:
                logger.error(f"Failed to load ledger: {e}")
                self.positions = {}

    def _save(self, force: bool = False):
        """
        Persist ledger to disk atomically with throttling.

        Args:
            force: Skip throttle check and save immediately
        """
        now = time.time()

        # Throttle saves unless forced
        if not force and (now - self.last_save_ts) < self.save_interval_seconds:
            return

        try:
            data = {
                'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
                'cooldown_until': self.cooldown_until,
                'trades_today': self.trades_today,
                'last_counter_date': self.last_counter_date,
                'closed_trades': [ct.to_dict() for ct in self.closed_trades[-self.max_closed_trades:]],
                'last_save': now
            }

            # Atomic write: temp file then rename
            tmp_path = self.ledger_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)

            os.replace(tmp_path, self.ledger_path)
            self.last_save_ts = now

        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

    def _auto_reset_daily_counters(self):
        """Auto-reset daily counters if date changed."""
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        if self.last_counter_date and self.last_counter_date != current_date:
            logger.info(f"Date changed from {self.last_counter_date} to {current_date} - resetting daily counters")
            self.trades_today = {}

        self.last_counter_date = current_date
        self._save(force=True)

    def get_position(self, symbol: str) -> Position:
        """Get current position for symbol. Returns FLAT if none exists."""
        return self.positions.get(symbol, Position(
            symbol=symbol,
            side='FLAT',
            size=0.0,
            entry_price=0.0,
            open_time=0.0,
            position_id=str(uuid.uuid4())
        ))

    def can_open_position(self, symbol: str, side: Literal['LONG', 'SHORT']) -> tuple[bool, str]:
        """
        CRITICAL CONFLICT CHECK.

        Returns (can_open, reason)
        """
        # Auto-reset if needed
        self._auto_reset_daily_counters()

        current = self.get_position(symbol)
        now = time.time()

        # 1. Check if symbol in desync (per-symbol safe mode)
        if symbol in self.desync_events:
            desync = self.desync_events[symbol]
            if (now - desync.first_seen_ts) > self.desync_grace_seconds:
                return False, f"Symbol in SAFE MODE: {desync.mismatch_type} - {desync.details}"

        # 2. Check cooldown
        if symbol in self.cooldown_until:
            cooldown_end = self.cooldown_until[symbol]
            if now < cooldown_end:
                remaining = int(cooldown_end - now)
                return False, f"Cooldown active: {remaining}s remaining"

        # 3. Check max trades per day
        if self.trades_today.get(symbol, 0) >= self.max_trades_per_day:
            return False, f"Max trades/day ({self.max_trades_per_day}) reached"

        # 4. CRITICAL: Check for opposite position
        if current.side == 'LONG' and side == 'SHORT':
            return False, f"❌ CONFLICT: Cannot SHORT while LONG position exists (size: {current.size})"

        if current.side == 'SHORT' and side == 'LONG':
            return False, f"❌ CONFLICT: Cannot LONG while SHORT position exists (size: {current.size})"

        # 5. Check if position already exists same side (no scaling)
        if current.side == side and current.size > 0:
            return False, f"Position already exists: {side} {current.size}"

        return True, "OK"

    def open_position(
        self,
        symbol: str,
        side: Literal['LONG', 'SHORT'],
        size: float,
        entry_price: float,
        client_order_id: Optional[str] = None,
        order_id: Optional[str] = None,
        entry_reason: Optional[str] = None,
        entry_regime: Optional[str] = None,
    ) -> bool:
        """
        Open new position (idempotent if same client_order_id).
        Returns True if successful.
        """
        # Idempotency check
        if client_order_id:
            existing = self.positions.get(symbol)
            if existing and existing.client_order_id == client_order_id:
                logger.debug(f"Position already recorded for client_order_id {client_order_id}")
                return True

        can_open, reason = self.can_open_position(symbol, side)

        if not can_open:
            logger.warning(f"Cannot open {side} on {symbol}: {reason}")
            return False

        normalized_entry_reason = str(entry_reason).strip() if entry_reason is not None else ""
        if not normalized_entry_reason:
            normalized_entry_reason = "unknown"
        normalized_entry_regime = str(entry_regime).strip().lower() if entry_regime is not None else ""
        if not normalized_entry_regime:
            normalized_entry_regime = "unknown"

        # Create position
        position_id = str(uuid.uuid4())
        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            open_time=time.time(),
            position_id=position_id,
            client_order_id=client_order_id,
            order_id=order_id,
            entry_reason=normalized_entry_reason,
            entry_regime=normalized_entry_regime,
            last_update_ts=time.time(),
            last_exchange_sync_ts=time.time()
        )

        # Increment trade count
        self.trades_today[symbol] = self.trades_today.get(symbol, 0) + 1

        # Clear cooldown and desync if any
        self.cooldown_until.pop(symbol, None)
        self.desync_events.pop(symbol, None)

        self._save()
        logger.info(
            f"✅ Opened {side} position on {symbol}: size={size}, price={entry_price}, id={position_id[:8]}, entry_reason={normalized_entry_reason}"
        )
        return True

    def close_position(
        self,
        symbol: str,
        close_price: float,
        realized_pnl: float,
        close_reason: str = 'manual',
        fees_estimated: float = 0.0
    ):
        """
        Close position and start cooldown.
        Records to closed_trades for learning.
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot close {symbol}: no position exists")
            return

        pos = self.positions[symbol]

        if pos.side == 'FLAT':
            logger.debug(f"{symbol} already FLAT")
            return

        # Record closed trade
        close_time = time.time()
        holding_seconds = close_time - pos.open_time
        normalized_entry_reason = str(pos.entry_reason).strip() if pos.entry_reason is not None else ""
        if not normalized_entry_reason:
            normalized_entry_reason = "unknown"
        normalized_entry_regime = str(pos.entry_regime).strip().lower() if pos.entry_regime is not None else ""
        if not normalized_entry_regime:
            normalized_entry_regime = "unknown"

        closed_trade = ClosedTrade(
            position_id=pos.position_id,
            symbol=symbol,
            side=pos.side,
            size=pos.size,
            entry_price=pos.entry_price,
            close_price=close_price,
            open_time=pos.open_time,
            close_time=close_time,
            holding_seconds=holding_seconds,
            realized_pnl=realized_pnl,
            close_reason=close_reason,
            entry_reason=normalized_entry_reason,
            entry_regime=normalized_entry_regime,
            fees_estimated=fees_estimated,
            pnl_is_net=False,
        )

        self.closed_trades.append(closed_trade)
        logger.info(
            "EXIT_ATTRIBUTION: symbol={} entry_reason={} exit_reason={} pnl={:.4f}",
            symbol,
            normalized_entry_reason,
            close_reason,
            realized_pnl,
        )

        # Log closure
        logger.info(f"✅ Closed {pos.side} position on {symbol}: "
                   f"entry={pos.entry_price:.2f}, close={close_price:.2f}, "
                   f"P&L=${realized_pnl:.2f}, holding={holding_seconds/60:.1f}min, reason={close_reason}")

        # Set to FLAT
        self.positions[symbol] = Position(
            symbol=symbol,
            side='FLAT',
            size=0.0,
            entry_price=0.0,
            open_time=0.0,
            position_id=str(uuid.uuid4()),
            entry_reason="unknown",
            entry_regime="unknown",
            realized_pnl=realized_pnl,
            last_update_ts=close_time
        )

        # Start cooldown (dynamic based on outcome)
        cooldown = self.cooldown_seconds
        if realized_pnl < 0:
            # Longer cooldown after loss (300-900s)
            cooldown = min(900, self.cooldown_seconds * 3)

        self.cooldown_until[symbol] = time.time() + cooldown

        self._save(force=True)

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
        self._save()  # Throttled

    def reconcile_with_exchange(self, exchange_positions: list) -> tuple[bool, List[str]]:
        """
        BIDIRECTIONAL reconciliation: ledger ↔ exchange.

        Returns (is_consistent, warnings)

        If inconsistent beyond grace period → SAFE MODE per symbol
        """
        logger.info("Reconciling position ledger with exchange (bidirectional)...")

        now = time.time()
        mismatches = []
        warnings = []

        # Build exchange map
        exchange_map = {}
        for pos_data in exchange_positions:
            symbol = pos_data['symbol']
            exchange_map[symbol] = {
                'side': pos_data['side'],  # 'LONG' or 'SHORT'
                'size': float(pos_data['size'])
            }

        # DIRECTION 1: Exchange → Ledger
        for symbol, exch_data in exchange_map.items():
            ledger_pos = self.get_position(symbol)

            # Check side mismatch
            if ledger_pos.side != exch_data['side']:
                mismatch = f"{symbol}: ledger={ledger_pos.side}, exchange={exch_data['side']}"
                mismatches.append(mismatch)
                self._record_desync(symbol, 'SIDE_MISMATCH', mismatch, now)

            # Check size mismatch
            elif abs(ledger_pos.size - exch_data['size']) > 0.001:
                mismatch = f"{symbol}: ledger size={ledger_pos.size}, exchange size={exch_data['size']}"
                mismatches.append(mismatch)
                self._record_desync(symbol, 'SIZE_MISMATCH', mismatch, now)

            else:
                # Match OK - clear any desync
                if symbol in self.desync_events:
                    logger.info(f"✅ {symbol} desync resolved")
                    self.desync_events.pop(symbol, None)

                # Update sync timestamp
                ledger_pos.last_exchange_sync_ts = now

        # DIRECTION 2: Ledger → Exchange (detect missing positions on exchange)
        ledger_open = {s: p for s, p in self.positions.items() if p.side != 'FLAT'}

        for symbol, ledger_pos in ledger_open.items():
            if symbol not in exchange_map:
                # Ledger thinks open but exchange shows FLAT
                mismatch = f"{symbol}: ledger={ledger_pos.side} but exchange=FLAT"

                # Check if desync is persistent
                if symbol in self.desync_events:
                    desync = self.desync_events[symbol]
                    if (now - desync.first_seen_ts) > self.desync_grace_seconds:
                        # Auto-close after grace period
                        logger.warning(f"⚠️ Auto-closing {symbol} - exchange confirmed FLAT after {self.desync_grace_seconds}s")
                        self.close_position(
                            symbol=symbol,
                            close_price=ledger_pos.entry_price,  # Unknown exit
                            realized_pnl=0.0,
                            close_reason='exchange_flat_detected'
                        )
                        warnings.append(f"Auto-closed {symbol} (exchange flat)")
                    else:
                        # Still in grace period
                        remaining = self.desync_grace_seconds - (now - desync.first_seen_ts)
                        warnings.append(f"{symbol} desync grace: {remaining:.0f}s remaining")
                else:
                    # First detection
                    self._record_desync(symbol, 'EXCHANGE_MISSING', mismatch, now)
                    warnings.append(f"New desync: {mismatch}")

        # Check for persistent desyncs beyond grace
        safe_mode_symbols = []
        for symbol, desync in list(self.desync_events.items()):
            if (now - desync.first_seen_ts) > self.desync_grace_seconds:
                if desync.mismatch_type in ['SIDE_MISMATCH', 'SIZE_MISMATCH']:
                    # Critical mismatch - symbol-level SAFE MODE
                    safe_mode_symbols.append(symbol)

        if safe_mode_symbols:
            logger.critical(f"❌ SAFE MODE for symbols: {safe_mode_symbols}")
            return False, warnings

        if mismatches:
            logger.warning(f"⚠️ Desyncs detected (within grace period): {mismatches}")
        else:
            logger.info("✅ Ledger reconciliation successful")

        self._save()
        return True, warnings

    def _record_desync(self, symbol: str, mismatch_type: str, details: str, ts: float):
        """Record or update desync event."""
        if symbol not in self.desync_events:
            self.desync_events[symbol] = DesyncEvent(
                symbol=symbol,
                first_seen_ts=ts,
                mismatch_type=mismatch_type,
                details=details
            )
            logger.warning(f"🔍 New desync detected: {details}")

    def get_all_positions(self) -> Dict[str, Position]:
        """Get all non-FLAT positions."""
        return {
            symbol: pos for symbol, pos in self.positions.items()
            if pos.side != 'FLAT'
        }

    def get_closed_trades(self, limit: int = 100) -> List[ClosedTrade]:
        """Get recent closed trades for analysis."""
        return self.closed_trades[-limit:]

    def get_recent_closed_trades(self, hours: int = 24, limit: int = 1000) -> List[ClosedTrade]:
        """Get closed trades in a rolling lookback window."""
        window_hours = max(1, int(hours))
        cutoff_ts = time.time() - (window_hours * 3600)
        recent = [trade for trade in self.closed_trades if float(trade.close_time) >= cutoff_ts]
        if limit > 0:
            return recent[-int(limit):]
        return recent

    def record_closed_trade(
        self,
        symbol: str,
        side: PositionSide,
        size: float,
        entry_price: float,
        close_price: float,
        realized_pnl: float,
        close_reason: str,
        entry_reason: Optional[str] = None,
        entry_regime: Optional[str] = None,
        fees_estimated: float = 0.0,
        pnl_is_net: bool = False,
        open_time: Optional[float] = None,
        close_time: Optional[float] = None,
        position_id: Optional[str] = None,
    ) -> bool:
        """Append an externally-resolved close event (e.g. straddle lifecycle)."""
        close_ts = float(close_time) if close_time is not None else time.time()
        open_ts = float(open_time) if open_time is not None else close_ts
        if open_ts > close_ts:
            open_ts = close_ts
        if side not in ("LONG", "SHORT", "FLAT"):
            side = "LONG"
        pos_id = position_id or str(uuid.uuid4())
        if any(existing.position_id == pos_id for existing in self.closed_trades[-self.max_closed_trades:]):
            logger.debug("Skipping duplicate closed trade record position_id={}", pos_id)
            return False

        normalized_entry_reason = str(entry_reason).strip() if entry_reason is not None else ""
        if not normalized_entry_reason:
            normalized_entry_reason = "unknown"
        normalized_entry_regime = str(entry_regime).strip().lower() if entry_regime is not None else ""
        if not normalized_entry_regime:
            normalized_entry_regime = "unknown"

        holding_seconds = max(0.0, close_ts - open_ts)
        closed_trade = ClosedTrade(
            position_id=pos_id,
            symbol=symbol,
            side=side,
            size=float(size),
            entry_price=float(entry_price),
            close_price=float(close_price),
            open_time=open_ts,
            close_time=close_ts,
            holding_seconds=holding_seconds,
            realized_pnl=float(realized_pnl),
            close_reason=str(close_reason or "manual"),
            entry_reason=normalized_entry_reason,
            entry_regime=normalized_entry_regime,
            fees_estimated=float(fees_estimated or 0.0),
            pnl_is_net=bool(pnl_is_net),
        )
        self.closed_trades.append(closed_trade)
        self._save(force=True)
        logger.info(
            "LEDGER_CLOSED_TRADE_RECORDED symbol={} entry_reason={} regime={} exit_reason={} pnl={:.4f} pnl_is_net={}",
            symbol,
            normalized_entry_reason,
            normalized_entry_regime,
            close_reason,
            float(realized_pnl),
            bool(pnl_is_net),
        )
        return True

    def export_closed_trades_csv(self, path: str):
        """Export closed trades to CSV for learning."""
        import csv

        with open(path, 'w', newline='') as f:
            if not self.closed_trades:
                return

            fieldnames = list(self.closed_trades[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for trade in self.closed_trades:
                writer.writerow(trade.to_dict())

        logger.info(f"Exported {len(self.closed_trades)} closed trades to {path}")
