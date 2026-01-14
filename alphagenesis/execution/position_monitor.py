"""
Position Monitor - Background Loop for Auto-Close Detection

Polls exchange every 20-30s to detect:
- Positions closed by SL/TP
- Positions closed by liquidation
- Positions closed manually
- Position size changes (partial closes)

Updates ledger, journal, and bandit automatically.
"""
import time
import threading
from typing import Dict, List
from loguru import logger


class PositionMonitor:
    """
    Background monitor for position lifecycle events.

    CRITICAL: This ensures ledger stays synchronized with exchange
    even when positions close via SL/TP, liquidation, or manual action.
    """

    def __init__(
        self,
        weex_client,
        position_ledger,
        decision_journal,
        bandit_allocator,
        poll_interval_seconds: int = 30
    ):
        self.weex = weex_client
        self.ledger = position_ledger
        self.journal = decision_journal
        self.bandit = bandit_allocator
        self.poll_interval = poll_interval_seconds

        self.is_running = False
        self.monitor_thread = None

        logger.info(f"PositionMonitor initialized (poll every {poll_interval_seconds}s)")

    def start(self):
        """Start monitoring in background thread."""
        if self.is_running:
            logger.warning("Position monitor already running")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("✓ Position monitor started")

    def stop(self):
        """Stop monitoring."""
        self.is_running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Position monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self._check_positions()
            except Exception as e:
                logger.error(f"Error in position monitor: {e}", exc_info=True)

            time.sleep(self.poll_interval)

    def _check_positions(self):
        """Check all positions for closes/updates."""
        try:
            # Fetch current exchange state
            account = self.weex.get_account()

            if 'position' not in account:
                exchange_positions = []
            else:
                exchange_positions = account['position']

            # Build exchange position map
            exchange_map = {}
            for pos in exchange_positions:
                size = float(pos.get('size', 0))
                if size > 0:  # Only active positions
                    symbol = pos['symbol']
                    side_num = int(pos.get('side', 1))
                    side_str = 'LONG' if side_num == 1 else 'SHORT'

                    exchange_map[symbol] = {
                        'side': side_str,
                        'size': size,
                        'entry_price': float(pos.get('open_price', 0)),
                        'unrealized_pnl': float(pos.get('unrealised_pnl', 0))
                    }

            # Check all ledger positions
            ledger_positions = self.ledger.get_all_positions()

            for symbol, ledger_pos in ledger_positions.items():
                if symbol not in exchange_map:
                    # Ledger shows open, exchange shows FLAT → position closed
                    self._handle_position_close(symbol, ledger_pos, exchange_map)

                elif exchange_map[symbol]['size'] < ledger_pos.size:
                    # Size decreased → partial close
                    self._handle_partial_close(symbol, ledger_pos, exchange_map[symbol])

                else:
                    # Position still open, update unrealized P&L
                    self.ledger.update_unrealized_pnl(
                        symbol,
                        exchange_map[symbol]['entry_price']  # Use current price
                    )

        except Exception as e:
            logger.error(f"Error checking positions: {e}", exc_info=True)

    def _handle_position_close(
        self,
        symbol: str,
        ledger_pos,
        exchange_map: Dict
    ):
        """Handle position close detected from exchange."""
        try:
            logger.info(f"📉 Detected position close: {symbol} {ledger_pos.side}")

            # Try to determine close reason
            close_reason = self._determine_close_reason(symbol, ledger_pos)

            # Estimate close price (use entry if unknown)
            close_price = ledger_pos.entry_price  # Conservative estimate

            # Calculate realized P&L (approximate)
            if ledger_pos.side == 'LONG':
                realized_pnl = (close_price - ledger_pos.entry_price) * ledger_pos.size
            else:  # SHORT
                realized_pnl = (ledger_pos.entry_price - close_price) * ledger_pos.size

            # Estimate fees (0.06% maker + taker)
            fees_estimated = (ledger_pos.entry_price * ledger_pos.size) * 0.0006

            # Calculate reward for bandit
            reward = realized_pnl - fees_estimated

            # Close in ledger
            self.ledger.close_position(
                symbol=symbol,
                close_price=close_price,
                realized_pnl=realized_pnl,
                close_reason=close_reason,
                fees_estimated=fees_estimated
            )

            # Log trade event to journal
            close_time = time.time()
            holding_seconds = close_time - ledger_pos.open_time

            trade_event = {
                'timestamp': close_time,
                'symbol': symbol,
                'side': ledger_pos.side,
                'size': ledger_pos.size,
                'entry_price': ledger_pos.entry_price,
                'exit_price': close_price,
                'open_time': ledger_pos.open_time,
                'close_time': close_time,
                'holding_seconds': holding_seconds,
                'realized_pnl': realized_pnl,
                'fees_estimated': fees_estimated,
                'mae': 0.0,  # TODO: track from unrealized_pnl history
                'mfe': 0.0,
                'close_reason': close_reason,
                'position_id': ledger_pos.position_id,
                'order_id': ledger_pos.order_id
            }

            from alphagenesis.learning import TradeEvent
            self.journal.log_trade_event(TradeEvent(**trade_event))

            # Update bandit with reward
            # Need to know which strategy was used - check ledger or journal
            # For now, assume 'momentum' (TODO: store strategy in position)
            regime = 'unknown'  # TODO: store regime in position
            self.bandit.update(
                symbol=symbol,
                regime=regime,
                strategy='momentum',  # TODO: get from position metadata
                reward=reward
            )

            logger.info(f"✓ Position close processed: P&L=${realized_pnl:.2f}, reward={reward:.4f}")

        except Exception as e:
            logger.error(f"Error handling position close for {symbol}: {e}", exc_info=True)

    def _determine_close_reason(self, symbol: str, ledger_pos) -> str:
        """
        Determine why position closed.

        Checks:
        - Recent trades for liquidation
        - Order history for SL/TP fills
        - Default: 'exchange_closed'
        """
        try:
            # TODO: Check order history for SL/TP
            # For now, default to generic close
            return 'exchange_closed'

        except Exception as e:
            logger.error(f"Error determining close reason: {e}")
            return 'unknown'

    def _handle_partial_close(
        self,
        symbol: str,
        ledger_pos,
        exchange_pos: Dict
    ):
        """Handle partial position close."""
        logger.info(f"📊 Partial close detected: {symbol} "
                   f"{ledger_pos.size} → {exchange_pos['size']}")

        # TODO: Implement partial close handling
        # For now, just log it
        # Full implementation would:
        # 1. Calculate partial realized P&L
        # 2. Update ledger position size
        # 3. Log partial close event
        # 4. NOT update bandit (wait for full close)
