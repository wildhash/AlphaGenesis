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
    initial_size: float = 0.0
    add_count: int = 0
    last_add_ts: float = 0.0

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
        self.post_open_confirm_until: Dict[str, float] = {}  # symbol -> unix ts
        self.sol_flat_detect_state: Dict[str, Dict[str, float]] = {}

        # Config
        self.cooldown_seconds = 180  # 3 minutes after close
        self.max_trades_per_day = 20  # Per symbol (reduced from 50 - fee control)
        self.allow_same_side_scale_in = str(
            os.getenv("ALLOW_SAME_SIDE_SCALE_IN", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}
        try:
            self.same_side_scale_in_max_adds = max(0, int(os.getenv("SAME_SIDE_SCALE_IN_MAX_ADDS", "0") or 0))
        except (TypeError, ValueError):
            self.same_side_scale_in_max_adds = 0
        try:
            self.same_side_scale_in_min_seconds = max(0, int(os.getenv("SAME_SIDE_SCALE_IN_MIN_SECONDS", "300") or 300))
        except (TypeError, ValueError):
            self.same_side_scale_in_min_seconds = 300
        try:
            self.same_side_scale_in_max_total_multiplier = max(1.0, float(os.getenv("SAME_SIDE_SCALE_IN_MAX_TOTAL_MULTIPLIER", "1.0") or 1.0))
        except (TypeError, ValueError):
            self.same_side_scale_in_max_total_multiplier = 1.0
        self.desync_grace_seconds = 30  # Wait 30s before SAFE MODE
        self.save_interval_seconds = 5  # Throttle saves
        self.max_closed_trades = 1000  # Keep last N for learning
        try:
            self.post_open_confirmation_seconds = max(
                0.0,
                float(os.getenv("POST_OPEN_CONFIRMATION_SECONDS", "10") or 10.0),
            )
        except (TypeError, ValueError):
            self.post_open_confirmation_seconds = 10.0
        self.sol_flat_detect_debounce_enabled = str(
            os.getenv("SOL_FLAT_DETECT_DEBOUNCE_ENABLED", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}
        try:
            self.sol_flat_detect_debounce_count = max(
                1,
                int(os.getenv("SOL_FLAT_DETECT_DEBOUNCE_COUNT", "3") or 3),
            )
        except (TypeError, ValueError):
            self.sol_flat_detect_debounce_count = 3
        try:
            self.sol_flat_detect_debounce_window_s = max(
                1.0,
                float(os.getenv("SOL_FLAT_DETECT_DEBOUNCE_WINDOW_S", "10") or 10.0),
            )
        except (TypeError, ValueError):
            self.sol_flat_detect_debounce_window_s = 10.0
        self.sol_size_mismatch_autosync_enabled = str(
            os.getenv("SOL_SIZE_MISMATCH_AUTOSYNC_ENABLED", "true")
        ).strip().lower() in {"1", "true", "yes", "on"}
        try:
            self.sol_size_mismatch_tolerance = max(
                0.0,
                float(os.getenv("SOL_SIZE_MISMATCH_TOLERANCE", "0.001") or 0.001),
            )
        except (TypeError, ValueError):
            self.sol_size_mismatch_tolerance = 0.001

        # State
        self.last_save_ts = 0.0
        self.last_counter_date = ""  # UTC date string for auto-reset

        self._load()
        self._auto_reset_daily_counters()
        if self.allow_same_side_scale_in:
            logger.warning(
                "SAME_SIDE_SCALE_IN_ENABLED max_adds={} min_seconds={} max_total_multiplier={}",
                self.same_side_scale_in_max_adds,
                self.same_side_scale_in_min_seconds,
                self.same_side_scale_in_max_total_multiplier,
            )
        logger.info(f"PositionLedger initialized with {len([p for p in self.positions.values() if p.side != 'FLAT'])} open positions")

    @staticmethod
    def _is_sol_symbol(symbol: str) -> bool:
        return str(symbol).strip().lower() == "cmt_solusdt"

    def _reset_sol_flat_detect_state(self, symbol: str, reason: str) -> None:
        state = self.sol_flat_detect_state.pop(symbol, None)
        if not self._is_sol_symbol(symbol):
            return
        if not state:
            return
        logger.info(
            "SOL_FLAT_DETECT_DEBOUNCE count={} window_s={} action=RELEASE reason={} symbol={}",
            int(state.get("count", 0) or 0),
            int(max(0.0, time.time() - float(state.get("first_seen_ts", time.time()) or time.time()))),
            reason,
            symbol,
        )

    def _update_sol_flat_detect_state(self, symbol: str, now_ts: float) -> tuple[int, float, bool]:
        state = self.sol_flat_detect_state.get(symbol) or {}
        first_seen_ts = float(state.get("first_seen_ts", 0.0) or 0.0)
        count = int(state.get("count", 0) or 0)
        if first_seen_ts <= 0.0 or (now_ts - first_seen_ts) > self.sol_flat_detect_debounce_window_s:
            first_seen_ts = now_ts
            count = 1
        else:
            count += 1
        self.sol_flat_detect_state[symbol] = {
            "first_seen_ts": first_seen_ts,
            "last_seen_ts": now_ts,
            "count": count,
        }
        age_s = max(0.0, now_ts - first_seen_ts)
        return count, age_s, count >= self.sol_flat_detect_debounce_count

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

    def can_open_position(self, symbol: str, side: Literal['LONG', 'SHORT'], requested_size: float = 0.0) -> tuple[bool, str]:
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

        # 5. Check if position already exists same side
        if current.side == side and current.size > 0:
            if not self.allow_same_side_scale_in:
                return False, f"Position already exists: {side} {current.size}"

            add_count = int(current.add_count or 0)
            if add_count >= self.same_side_scale_in_max_adds:
                return False, f"Scale-in cap reached: adds={add_count}, max={self.same_side_scale_in_max_adds}"

            last_add_ts = float(current.last_add_ts or current.open_time or 0.0)
            cooldown_remaining = self.same_side_scale_in_min_seconds - (now - last_add_ts)
            if cooldown_remaining > 0:
                return False, f"Scale-in cooldown active: {int(cooldown_remaining)}s remaining"

            try:
                requested = max(0.0, float(requested_size or 0.0))
            except (TypeError, ValueError):
                requested = 0.0

            base_size = float(current.initial_size or 0.0)
            if base_size <= 0.0:
                base_size = float(current.size or 0.0)
            max_total_size = base_size * self.same_side_scale_in_max_total_multiplier
            projected_size = float(current.size or 0.0) + requested
            if requested > 0.0 and projected_size > max_total_size:
                return False, (
                    f"Scale-in max_total exceeded: projected={projected_size:.4f} "
                    f"> cap={max_total_size:.4f} (base={base_size:.4f})"
                )

            return True, (
                f"SCALE_IN_ALLOWED side={side} add_count={add_count} "
                f"req={requested:.4f} max_total={max_total_size:.4f}"
            )

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

        can_open, reason = self.can_open_position(symbol, side, size)

        if not can_open:
            logger.warning(f"Cannot open {side} on {symbol}: {reason}")
            return False

        normalized_entry_reason = str(entry_reason).strip() if entry_reason is not None else ""
        if not normalized_entry_reason:
            normalized_entry_reason = "unknown"
        normalized_entry_regime = str(entry_regime).strip().lower() if entry_regime is not None else ""
        if not normalized_entry_regime:
            normalized_entry_regime = "unknown"

        current_pos = self.get_position(symbol)
        if self.allow_same_side_scale_in and current_pos.side == side and current_pos.size > 0:
            add_size = max(0.0, float(size or 0.0))
            if add_size <= 0.0:
                logger.warning(f"Cannot scale {side} on {symbol}: invalid add_size={add_size}")
                return False

            now_ts = time.time()
            old_size = float(current_pos.size or 0.0)
            old_entry = float(current_pos.entry_price or 0.0)
            new_size = old_size + add_size
            if new_size <= 0.0:
                logger.warning(f"Cannot scale {side} on {symbol}: invalid new_size={new_size}")
                return False

            weighted_entry = ((old_entry * old_size) + (float(entry_price) * add_size)) / new_size
            base_size = float(current_pos.initial_size or 0.0)
            if base_size <= 0.0:
                base_size = old_size

            current_pos.size = new_size
            current_pos.entry_price = weighted_entry
            current_pos.client_order_id = client_order_id or current_pos.client_order_id
            current_pos.order_id = order_id or current_pos.order_id
            current_pos.entry_reason = normalized_entry_reason
            current_pos.entry_regime = normalized_entry_regime
            current_pos.last_update_ts = now_ts
            current_pos.last_exchange_sync_ts = now_ts
            current_pos.initial_size = base_size
            current_pos.add_count = int(current_pos.add_count or 0) + 1
            current_pos.last_add_ts = now_ts

            self.positions[symbol] = current_pos
            self.trades_today[symbol] = self.trades_today.get(symbol, 0) + 1
            self.cooldown_until.pop(symbol, None)
            self.desync_events.pop(symbol, None)
            self.post_open_confirm_until.pop(symbol, None)
            if self.post_open_confirmation_seconds > 0:
                confirm_until = now_ts + self.post_open_confirmation_seconds
                self.post_open_confirm_until[symbol] = confirm_until
                logger.info(
                    "POST_OPEN_CONFIRMATION_ARMED symbol={} until={} window_s={}",
                    symbol,
                    int(confirm_until),
                    int(self.post_open_confirmation_seconds),
                )

            self._save()
            logger.warning(
                "✅ Scaled into {} position on {}: add_size={}, old_size={}, new_size={}, old_entry={}, new_entry={}, add_count={}",
                side,
                symbol,
                add_size,
                old_size,
                new_size,
                old_entry,
                weighted_entry,
                current_pos.add_count,
            )
            return True

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
            last_exchange_sync_ts=time.time(),
            initial_size=size,
            add_count=0,
            last_add_ts=time.time(),
        )

        # Increment trade count
        self.trades_today[symbol] = self.trades_today.get(symbol, 0) + 1

        # Clear cooldown and desync if any
        self.cooldown_until.pop(symbol, None)
        self.desync_events.pop(symbol, None)
        self.post_open_confirm_until.pop(symbol, None)
        if self.post_open_confirmation_seconds > 0:
            confirm_until = time.time() + self.post_open_confirmation_seconds
            self.post_open_confirm_until[symbol] = confirm_until
            logger.info(
                "POST_OPEN_CONFIRMATION_ARMED symbol={} until={} window_s={}",
                symbol,
                int(confirm_until),
                int(self.post_open_confirmation_seconds),
            )

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
        self.post_open_confirm_until.pop(symbol, None)

        self._save(force=True)

    def force_close_position(
        self,
        symbol: str,
        realized_pnl: float = 0.0,
        reason: str = "manual_force_close",
        close_price: Optional[float] = None,
        fees_estimated: float = 0.0,
    ) -> bool:
        """
        Force-close a position using current ledger state.
        Useful for reconciliation when exchange reports FLAT.
        """
        pos = self.get_position(symbol)
        if pos.side == "FLAT" or pos.size <= 0:
            logger.info("FORCE_CLOSE_POSITION_NOOP symbol={} already_flat_or_empty", symbol)
            return False

        resolved_close_price = float(close_price) if close_price is not None else 0.0
        if resolved_close_price <= 0:
            resolved_close_price = float(pos.entry_price or 0.0)
        if resolved_close_price <= 0:
            resolved_close_price = 1e-9

        self.close_position(
            symbol=symbol,
            close_price=resolved_close_price,
            realized_pnl=float(realized_pnl or 0.0),
            close_reason=str(reason or "manual_force_close"),
            fees_estimated=float(fees_estimated or 0.0),
        )
        logger.warning(
            "FORCE_CLOSE_POSITION_APPLIED symbol={} reason={} close_price={} realized_pnl={}",
            symbol,
            reason,
            resolved_close_price,
            float(realized_pnl or 0.0),
        )
        return True

    def adjust_position_size(
        self,
        symbol: str,
        new_size: float,
        avg_price: Optional[float] = None,
        reason: str = "reconciliation",
    ) -> bool:
        """
        Synchronize ledger size to exchange-reported size without changing side.
        """
        pos = self.get_position(symbol)
        if pos.side == "FLAT":
            logger.warning(
                "ADJUST_POSITION_SIZE_SKIPPED symbol={} reason=flat_position",
                symbol,
            )
            return False

        target_size = max(0.0, float(new_size or 0.0))
        if target_size <= 0.0:
            logger.warning(
                "ADJUST_POSITION_SIZE_TO_ZERO symbol={} reason={} -> force close",
                symbol,
                reason,
            )
            return self.force_close_position(
                symbol=symbol,
                realized_pnl=0.0,
                reason=f"{reason}_size_zero",
                close_price=avg_price if avg_price is not None else pos.entry_price,
            )

        old_size = float(pos.size or 0.0)
        if abs(old_size - target_size) <= 0.001:
            logger.info(
                "ADJUST_POSITION_SIZE_NOOP symbol={} size={} reason={}",
                symbol,
                target_size,
                reason,
            )
            return False

        old_entry = float(pos.entry_price or 0.0)
        if avg_price is not None:
            try:
                normalized_avg = float(avg_price)
                if normalized_avg > 0:
                    pos.entry_price = normalized_avg
            except (TypeError, ValueError):
                pass

        pos.size = target_size
        pos.last_update_ts = time.time()
        pos.last_exchange_sync_ts = pos.last_update_ts

        if symbol in self.desync_events:
            self.desync_events.pop(symbol, None)

        self._save(force=True)
        logger.warning(
            "LEDGER_POSITION_SIZE_SYNCED symbol={} old_size={} new_size={} old_entry={} new_entry={} reason={}",
            symbol,
            old_size,
            target_size,
            old_entry,
            pos.entry_price,
            reason,
        )
        return True

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
            self._reset_sol_flat_detect_state(symbol, reason="exchange_position_seen")

            # Check side mismatch
            if ledger_pos.side != exch_data['side']:
                mismatch = f"{symbol}: ledger={ledger_pos.side}, exchange={exch_data['side']}"
                mismatches.append(mismatch)
                self._record_desync(symbol, 'SIDE_MISMATCH', mismatch, now)

            # Check size mismatch
            elif abs(ledger_pos.size - exch_data['size']) > self.sol_size_mismatch_tolerance:
                mismatch = f"{symbol}: ledger size={ledger_pos.size}, exchange size={exch_data['size']}"
                symbol_norm = str(symbol).strip().lower()
                if (
                    symbol_norm == "cmt_solusdt"
                    and self.sol_size_mismatch_autosync_enabled
                    and ledger_pos.side == exch_data['side']
                ):
                    old_size = float(ledger_pos.size or 0.0)
                    new_size = float(exch_data['size'] or 0.0)
                    ledger_pos.size = new_size
                    ledger_pos.last_exchange_sync_ts = now
                    self.desync_events.pop(symbol, None)
                    logger.warning(
                        "SOL_SIZE_MISMATCH_AUTOSYNC symbol={} ledger_size_old={} exchange_size={} tolerance={}",
                        symbol,
                        old_size,
                        new_size,
                        self.sol_size_mismatch_tolerance,
                    )
                    continue
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
                confirm_until = float(self.post_open_confirm_until.get(symbol, 0.0) or 0.0)
                if confirm_until > now:
                    remaining = max(0.0, confirm_until - now)
                    self._reset_sol_flat_detect_state(symbol, reason="confirmation_window")
                    if str(symbol).strip().lower() == "cmt_solusdt":
                        logger.info(
                            "SOL_CONFIRM_WINDOW_SUPPRESS_FLATTEN symbol={} remaining_s={} ledger={} exchange=FLAT",
                            symbol,
                            int(remaining),
                            ledger_pos.side,
                        )
                    warnings.append(f"{symbol} confirmation window: {remaining:.0f}s remaining")
                    continue
                if confirm_until > 0.0:
                    self.post_open_confirm_until.pop(symbol, None)
                symbol_norm = str(symbol).strip().lower()
                debounce_triggered = True
                if symbol_norm == "cmt_solusdt" and self.sol_flat_detect_debounce_enabled:
                    debounce_count, debounce_age_s, debounce_triggered = self._update_sol_flat_detect_state(symbol, now)
                    logger.info(
                        "SOL_FLAT_DETECT_DEBOUNCE count={} window_s={} action={} symbol={} ledger={} exchange=FLAT",
                        debounce_count,
                        int(debounce_age_s),
                        "ARMED" if debounce_triggered else "SKIP",
                        symbol,
                        ledger_pos.side,
                    )
                if str(symbol).strip().lower() == "cmt_solusdt":
                    try:
                        position_age_s = max(0.0, now - float(ledger_pos.open_time or 0.0))
                    except (TypeError, ValueError):
                        position_age_s = 0.0
                    logger.info(
                        "SOL_LIFECYCLE_EVENT event=desync_detected symbol={} ledger_side={} exchange_side=FLAT position_age_s={} confirm_window_remaining_s=0",
                        symbol,
                        ledger_pos.side,
                        int(position_age_s),
                    )

                # Check if desync is persistent
                if symbol in self.desync_events:
                    desync = self.desync_events[symbol]
                    if (now - desync.first_seen_ts) > self.desync_grace_seconds:
                        if symbol_norm == "cmt_solusdt" and self.sol_flat_detect_debounce_enabled and not debounce_triggered:
                            warnings.append(
                                f"{symbol} flat-detect debounce: waiting {self.sol_flat_detect_state.get(symbol, {}).get('count', 0):.0f}/{self.sol_flat_detect_debounce_count}"
                            )
                            continue
                        # Auto-close after grace period
                        logger.warning(f"⚠️ Auto-closing {symbol} - exchange confirmed FLAT after {self.desync_grace_seconds}s")
                        self.close_position(
                            symbol=symbol,
                            close_price=ledger_pos.entry_price,  # Unknown exit
                            realized_pnl=0.0,
                            close_reason='exchange_flat_detected'
                        )
                        if str(symbol).strip().lower() == "cmt_solusdt":
                            logger.warning(
                                "SOL_FLAT_DETECT_DEBOUNCE count={} window_s={} action=TRIGGER symbol={} ledger={} exchange=FLAT",
                                int(self.sol_flat_detect_state.get(symbol, {}).get("count", 0) or 0),
                                int(max(0.0, now - float(self.sol_flat_detect_state.get(symbol, {}).get("first_seen_ts", now) or now))),
                                symbol,
                                ledger_pos.side,
                            )
                            logger.warning(
                                "SOL_LIFECYCLE_EVENT event=exchange_flat_autoclose symbol={} ledger_side={} exchange_side=FLAT",
                                symbol,
                                ledger_pos.side,
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
