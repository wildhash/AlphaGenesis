"""
Decision Journal - Training Data Collection

Logs every trading decision with:
- Market state / features
- Strategy signals
- Gate results (ledger, risk)
- Execution outcome
- Realized P&L

This becomes the training dataset for online learning and model improvement.
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class DecisionTick:
    """Single decision record."""
    timestamp: float
    symbol: str
    regime: str
    price: float

    # Features
    rsi: float
    ema_fast: float
    ema_slow: float
    volume: float
    volatility: float

    # Signal
    strategy_name: str
    signal_direction: str  # 'LONG', 'SHORT', 'HOLD'
    signal_confidence: float

    # Proposed action
    proposed_side: Optional[str]
    proposed_size: Optional[float]
    proposed_entry: Optional[float]
    proposed_stop: Optional[float]
    proposed_take_profit: Optional[float]

    # Gates
    ledger_approved: bool
    ledger_reason: str
    risk_approved: bool
    risk_veto_reasons: str  # JSON

    # Execution
    executed: bool
    execution_reason: str  # 'placed', 'ledger_blocked', 'risk_veto', 'intent_rejected'

    # Outcome (filled later when position closes)
    order_id: Optional[str] = None
    realized_pnl: Optional[float] = None
    fees_paid: Optional[float] = None
    holding_time: Optional[float] = None

    # Reward signal
    reward: Optional[float] = None


@dataclass
class TradeEvent:
    """Trade execution and close event."""
    timestamp: float
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: Optional[float]

    open_time: float
    close_time: Optional[float]
    holding_seconds: Optional[float]

    realized_pnl: float
    fees_estimated: float

    # Performance metrics
    mae: float  # Max Adverse Excursion
    mfe: float  # Max Favorable Excursion

    close_reason: str
    position_id: str
    order_id: Optional[str] = None


class DecisionJournal:
    """
    Persistent decision and trade logging to SQLite.

    Schema:
    - decision_ticks: Every decision point (whether traded or not)
    - trade_events: Actual trade opens/closes
    """

    def __init__(self, db_path: str = "/tmp/trading_journal.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()

        logger.info(f"DecisionJournal initialized at {self.db_path}")

    def _create_tables(self):
        """Create journal tables if not exist."""
        cursor = self.conn.cursor()

        # Decision ticks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                symbol TEXT,
                regime TEXT,
                price REAL,

                rsi REAL,
                ema_fast REAL,
                ema_slow REAL,
                volume REAL,
                volatility REAL,

                strategy_name TEXT,
                signal_direction TEXT,
                signal_confidence REAL,

                proposed_side TEXT,
                proposed_size REAL,
                proposed_entry REAL,
                proposed_stop REAL,
                proposed_take_profit REAL,

                ledger_approved INTEGER,
                ledger_reason TEXT,
                risk_approved INTEGER,
                risk_veto_reasons TEXT,

                executed INTEGER,
                execution_reason TEXT,

                order_id TEXT,
                realized_pnl REAL,
                fees_paid REAL,
                holding_time REAL,
                reward REAL
            )
        """)

        # Trade events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                symbol TEXT,
                side TEXT,
                size REAL,
                entry_price REAL,
                exit_price REAL,

                open_time REAL,
                close_time REAL,
                holding_seconds REAL,

                realized_pnl REAL,
                fees_estimated REAL,

                mae REAL,
                mfe REAL,

                close_reason TEXT,
                position_id TEXT,
                order_id TEXT
            )
        """)

        # Indices for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_timestamp
            ON decision_ticks(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_symbol
            ON decision_ticks(symbol)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trade_timestamp
            ON trade_events(timestamp)
        """)

        self.conn.commit()
        logger.info("Journal tables created/verified")

    def log_decision(self, decision: DecisionTick):
        """Log a decision tick."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO decision_ticks (
                timestamp, symbol, regime, price,
                rsi, ema_fast, ema_slow, volume, volatility,
                strategy_name, signal_direction, signal_confidence,
                proposed_side, proposed_size, proposed_entry, proposed_stop, proposed_take_profit,
                ledger_approved, ledger_reason, risk_approved, risk_veto_reasons,
                executed, execution_reason,
                order_id, realized_pnl, fees_paid, holding_time, reward
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.timestamp, decision.symbol, decision.regime, decision.price,
            decision.rsi, decision.ema_fast, decision.ema_slow, decision.volume, decision.volatility,
            decision.strategy_name, decision.signal_direction, decision.signal_confidence,
            decision.proposed_side, decision.proposed_size, decision.proposed_entry,
            decision.proposed_stop, decision.proposed_take_profit,
            int(decision.ledger_approved), decision.ledger_reason,
            int(decision.risk_approved), decision.risk_veto_reasons,
            int(decision.executed), decision.execution_reason,
            decision.order_id, decision.realized_pnl, decision.fees_paid,
            decision.holding_time, decision.reward
        ))

        self.conn.commit()

    def log_trade_event(self, trade: TradeEvent):
        """Log a trade open/close event."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trade_events (
                timestamp, symbol, side, size, entry_price, exit_price,
                open_time, close_time, holding_seconds,
                realized_pnl, fees_estimated,
                mae, mfe,
                close_reason, position_id, order_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.timestamp, trade.symbol, trade.side, trade.size,
            trade.entry_price, trade.exit_price,
            trade.open_time, trade.close_time, trade.holding_seconds,
            trade.realized_pnl, trade.fees_estimated,
            trade.mae, trade.mfe,
            trade.close_reason, trade.position_id, trade.order_id
        ))

        self.conn.commit()

    def update_decision_outcome(
        self,
        order_id: str,
        realized_pnl: float,
        fees_paid: float,
        holding_time: float,
        reward: float
    ):
        """Update decision record with outcome after position close."""
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE decision_ticks
            SET realized_pnl = ?, fees_paid = ?, holding_time = ?, reward = ?
            WHERE order_id = ?
        """, (realized_pnl, fees_paid, holding_time, reward, order_id))

        self.conn.commit()

    def get_recent_decisions(self, limit: int = 100) -> List[Dict]:
        """Get recent decision records."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM decision_ticks
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    def get_recent_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent trade events."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM trade_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    def get_strategy_performance(self, strategy_name: str, lookback_hours: int = 24) -> Dict:
        """Analyze strategy performance."""
        import time
        cutoff = time.time() - (lookback_hours * 3600)

        cursor = self.conn.cursor()

        # Get all decisions for this strategy
        cursor.execute("""
            SELECT
                COUNT(*) as total_decisions,
                SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed_count,
                AVG(CASE WHEN executed = 1 AND realized_pnl IS NOT NULL THEN realized_pnl ELSE NULL END) as avg_pnl,
                SUM(CASE WHEN executed = 1 AND realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN executed = 1 AND realized_pnl < 0 THEN 1 ELSE 0 END) as losses
            FROM decision_ticks
            WHERE strategy_name = ? AND timestamp > ?
        """, (strategy_name, cutoff))

        row = cursor.fetchone()

        return {
            'strategy_name': strategy_name,
            'total_decisions': row[0] or 0,
            'executed_count': row[1] or 0,
            'avg_pnl': row[2] or 0.0,
            'wins': row[3] or 0,
            'losses': row[4] or 0,
            'win_rate': (row[3] or 0) / max(1, (row[3] or 0) + (row[4] or 0))
        }

    def export_training_data(self, output_path: str, min_reward_samples: int = 100):
        """Export training dataset to CSV."""
        import csv

        cursor = self.conn.cursor()

        # Get all decisions with rewards (completed trades)
        cursor.execute("""
            SELECT * FROM decision_ticks
            WHERE reward IS NOT NULL
            ORDER BY timestamp
        """)

        rows = cursor.fetchall()

        if len(rows) < min_reward_samples:
            logger.warning(f"Only {len(rows)} samples with rewards, need {min_reward_samples}")
            return

        columns = [desc[0] for desc in cursor.description]

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for row in rows:
                writer.writerow(dict(zip(columns, row)))

        logger.info(f"Exported {len(rows)} training samples to {output_path}")

    def get_stats(self) -> Dict:
        """Get journal statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM decision_ticks")
        total_decisions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM decision_ticks WHERE executed = 1")
        executed_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trade_events")
        total_trades = cursor.fetchone()[0]

        cursor.execute("""
            SELECT SUM(realized_pnl) FROM trade_events
            WHERE realized_pnl IS NOT NULL
        """)
        total_pnl = cursor.fetchone()[0] or 0.0

        return {
            'total_decisions': total_decisions,
            'executed_count': executed_count,
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'execution_rate': executed_count / max(1, total_decisions)
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("DecisionJournal closed")
