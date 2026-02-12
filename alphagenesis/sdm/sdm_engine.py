"""
SDM Trading Engine - The Integration Point

This is where Intent becomes Execution through Semantic Dataflow.

Architecture Flow:
1. Intent Graph defines WHAT we want (goals, constraints)
2. Semantic Binding Layer resolves HOW (which models/strategies)
3. Constraint Propagation ensures SAFETY (potential fields)
4. Ethics Engine enforces PRINCIPLES (first-class constraints)
5. Continuous Learning ensures ADAPTATION (self-improvement)

No main(). No entry point. No termination.
Just continuous resolution under pressure.
"""

import os
import time
import signal
import json
import sqlite3
import random
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict
import numpy as np
from loguru import logger


class AILogBusWithExitSummary:
    def __init__(self, base_bus, record_cb: Callable[[str, Optional[float]], None]):
        self._base_bus = base_bus
        self._record_cb = record_cb

    def emit(self, stage: str, model: str, input_payload: Dict[str, Any], output_payload: Dict[str, Any], explanation: str, order_id: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        reason = None
        age_s = None
        if isinstance(input_payload, dict):
            reason = input_payload.get('exit_reason') or reason
            age_s = input_payload.get('age_seconds') or input_payload.get('age_s') or age_s
        if reason is None and isinstance(output_payload, dict):
            reason = output_payload.get('exit_reason')
        if reason:
            try:
                age_val = float(age_s) if age_s is not None else None
            except (TypeError, ValueError):
                age_val = None
            self._record_cb(reason, age_val)
        return self._base_bus.emit(stage, model, input_payload, output_payload, explanation, order_id=order_id, meta=meta)


class LoserTupleKillSwitch:
    """Auto-block weak (symbol, entry_reason, regime) tuples from recent realized exits."""

    def __init__(
        self,
        db_path: str,
        state_path: str,
        lookback_hours: int = 24,
        min_trades: int = 5,
        min_win_rate: float = 0.35,
        min_profit_factor: float = 0.80,
        max_total_pnl: float = -20.0,
        refresh_interval_seconds: int = 300,
    ):
        self.db_path = db_path
        self.state_path = state_path
        self.lookback_hours = max(1, int(lookback_hours))
        self.min_trades = max(1, int(min_trades))
        self.min_win_rate = float(min_win_rate)
        self.min_profit_factor = float(min_profit_factor)
        self.max_total_pnl = float(max_total_pnl)
        self.refresh_interval_seconds = max(30, int(refresh_interval_seconds))
        self.last_refresh_ts = 0.0
        self.blocked_tuples: Dict[str, Dict[str, Any]] = {}
        self._load_state()

    def _normalize_reason(self, value: Any) -> str:
        if value is None:
            return "LEGACY_NONE"
        reason = str(value).strip()
        return reason if reason else "LEGACY_NONE"

    def _normalize_regime(self, value: Any) -> str:
        if value is None:
            return "unknown"
        regime = str(value).strip().lower()
        return regime if regime else "unknown"

    def _tuple_key(self, symbol: Any, entry_reason: Any, regime: Any) -> str:
        symbol_norm = str(symbol or "unknown").strip().lower() or "unknown"
        reason_norm = self._normalize_reason(entry_reason)
        regime_norm = self._normalize_regime(regime)
        return f"{symbol_norm}|{reason_norm}|{regime_norm}"

    def _load_state(self) -> None:
        try:
            if not os.path.exists(self.state_path):
                return
            with open(self.state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                blocked = data.get("blocked_tuples")
                if isinstance(blocked, dict):
                    self.blocked_tuples = blocked
        except Exception as exc:
            logger.warning("LOSER_KILL_SWITCH_STATE_LOAD_FAILED path={} err={}", self.state_path, exc)

    def _save_state(self) -> None:
        try:
            tmp_path = f"{self.state_path}.tmp"
            payload = {
                "updated_at_ms": int(time.time() * 1000),
                "blocked_tuples": self.blocked_tuples,
            }
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=True, separators=(",", ":"))
            os.replace(tmp_path, self.state_path)
        except Exception as exc:
            logger.warning("LOSER_KILL_SWITCH_STATE_SAVE_FAILED path={} err={}", self.state_path, exc)

    def is_blocked(self, symbol: Any, entry_reason: Any, regime: Any) -> bool:
        return self._tuple_key(symbol, entry_reason, regime) in self.blocked_tuples

    def blocked_count(self) -> int:
        return len(self.blocked_tuples)

    def get_block_meta(self, symbol: Any, entry_reason: Any, regime: Any) -> Dict[str, Any]:
        return self.blocked_tuples.get(self._tuple_key(symbol, entry_reason, regime), {})

    def _accumulate_trade(self, stats: Dict[str, Dict[str, Any]], symbol: Any, entry_reason: Any, regime: Any, pnl: float) -> None:
        symbol_norm = str(symbol or "").lower().strip()
        if not symbol_norm:
            return
        reason_norm = self._normalize_reason(entry_reason)
        regime_norm = self._normalize_regime(regime)
        key = self._tuple_key(symbol_norm, reason_norm, regime_norm)
        st = stats[key]
        st["symbol"] = symbol_norm
        st["entry_reason"] = reason_norm
        st["regime"] = regime_norm
        st["n"] += 1
        st["total_pnl"] += pnl
        if pnl > 0:
            st["wins"] += 1
            st["gross_profit"] += pnl
        elif pnl < 0:
            st["gross_loss"] += abs(pnl)

    def _obj_get(self, obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _ingest_from_ledger(
        self,
        position_ledger: Any,
        cutoff_ts: float,
        stats: Dict[str, Dict[str, Any]],
    ) -> tuple[int, int, int, int, int, int]:
        total_rows = 0
        used_rows = 0
        skipped_no_pnl = 0
        skipped_flat_reason = 0
        skipped_near_zero = 0
        skipped_exchange_closed_unknown = 0
        min_abs_pnl = max(0.0, float(os.getenv("KILL_SWITCH_MIN_ABS_PNL", "0.001")))
        try:
            if hasattr(position_ledger, "get_recent_closed_trades"):
                trades = position_ledger.get_recent_closed_trades(hours=self.lookback_hours, limit=5000)
            elif hasattr(position_ledger, "get_closed_trades"):
                trades = position_ledger.get_closed_trades(limit=5000)
            else:
                return total_rows, used_rows, skipped_no_pnl, skipped_flat_reason, skipped_near_zero, skipped_exchange_closed_unknown
        except Exception as exc:
            logger.warning("LOSER_KILL_SWITCH_LEDGER_READ_FAILED err={}", exc)
            return total_rows, used_rows, skipped_no_pnl, skipped_flat_reason, skipped_near_zero, skipped_exchange_closed_unknown

        for trade in trades:
            total_rows += 1
            close_time = self._obj_get(trade, "close_time")
            try:
                if close_time is not None and float(close_time) < cutoff_ts:
                    continue
            except (TypeError, ValueError):
                continue

            close_reason = str(self._obj_get(trade, "close_reason") or "").strip().lower()
            if close_reason == "exchange_flat_detected":
                skipped_flat_reason += 1
                continue

            symbol = self._obj_get(trade, "symbol")
            entry_reason = self._obj_get(trade, "entry_reason")
            regime = self._obj_get(trade, "entry_regime")
            entry_reason_norm = self._normalize_reason(entry_reason).lower()
            regime_norm = self._normalize_regime(regime).lower()
            if close_reason == "exchange_closed" and entry_reason_norm in {"legacy_none", "unknown", "none"} and regime_norm in {"unknown", "none"}:
                skipped_exchange_closed_unknown += 1
                continue
            pnl_value = self._obj_get(trade, "realized_pnl")
            fees_estimated = self._obj_get(trade, "fees_estimated", 0.0)
            pnl_is_net = bool(self._obj_get(trade, "pnl_is_net", False))
            if pnl_value is None:
                skipped_no_pnl += 1
                continue
            try:
                pnl_float = float(pnl_value)
            except (TypeError, ValueError):
                skipped_no_pnl += 1
                continue
            try:
                fees_float = float(fees_estimated or 0.0)
            except (TypeError, ValueError):
                fees_float = 0.0
            if not pnl_is_net:
                pnl_float -= fees_float
            if min_abs_pnl > 0.0 and abs(pnl_float) < min_abs_pnl:
                skipped_near_zero += 1
                continue
            self._accumulate_trade(stats, symbol, entry_reason, regime, pnl_float)
            used_rows += 1
        return total_rows, used_rows, skipped_no_pnl, skipped_flat_reason, skipped_near_zero, skipped_exchange_closed_unknown

    def _ingest_from_ai_logs(self, since_ms: int, stats: Dict[str, Dict[str, Any]]) -> tuple[int, int, int, int, int, int]:
        total_rows = 0
        used_rows = 0
        skipped_no_pnl = 0
        skipped_flat_reason = 0
        skipped_near_zero = 0
        skipped_exchange_closed_unknown = 0
        min_abs_pnl = max(0.0, float(os.getenv("KILL_SWITCH_MIN_ABS_PNL", "0.001")))
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT created_at_ms, payload_json
            FROM ai_logs
            WHERE status='done'
              AND stage='Exit Execution'
              AND created_at_ms >= ?
        """
        for _, payload_json in conn.execute(query, (since_ms,)):
            total_rows += 1
            try:
                payload = json.loads(payload_json)
            except Exception:
                continue
            inp = payload.get("input", {}) if isinstance(payload, dict) else {}
            out = payload.get("output", {}) if isinstance(payload, dict) else {}
            symbol = inp.get("symbol") or out.get("symbol")
            entry_reason = inp.get("entry_reason") or out.get("entry_reason")
            if entry_reason is None and isinstance(inp.get("entry_meta"), dict):
                entry_reason = inp.get("entry_meta", {}).get("entry_reason")
            regime = (
                inp.get("regime")
                or out.get("regime")
                or (inp.get("entry_meta", {}).get("regime") if isinstance(inp.get("entry_meta"), dict) else None)
            )
            exit_reason = str(inp.get("exit_reason") or out.get("exit_reason") or "").strip().lower()
            if exit_reason == "exchange_flat_detected":
                skipped_flat_reason += 1
                continue
            entry_reason_norm = self._normalize_reason(entry_reason).lower()
            regime_norm = self._normalize_regime(regime).lower()
            if exit_reason == "exchange_closed" and entry_reason_norm in {"legacy_none", "unknown", "none"} and regime_norm in {"unknown", "none"}:
                skipped_exchange_closed_unknown += 1
                continue
            pnl = out.get("realized_pnl")
            if pnl is None:
                pnl = inp.get("realized_pnl")
            if pnl is None:
                skipped_no_pnl += 1
                continue
            try:
                pnl_float = float(pnl)
            except (TypeError, ValueError):
                skipped_no_pnl += 1
                continue
            if min_abs_pnl > 0.0 and abs(pnl_float) < min_abs_pnl:
                skipped_near_zero += 1
                continue
            self._accumulate_trade(stats, symbol, entry_reason, regime, pnl_float)
            used_rows += 1
        conn.close()
        return total_rows, used_rows, skipped_no_pnl, skipped_flat_reason, skipped_near_zero, skipped_exchange_closed_unknown

    def refresh(self, force: bool = False, position_ledger: Optional[Any] = None) -> int:
        now = time.time()
        if not force and (now - self.last_refresh_ts) < self.refresh_interval_seconds:
            return 0
        self.last_refresh_ts = now

        since_ms = int((now - (self.lookback_hours * 3600)) * 1000)
        cutoff_ts = now - (self.lookback_hours * 3600)
        stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "n": 0,
                "wins": 0,
                "total_pnl": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "symbol": "unknown",
                "entry_reason": "LEGACY_NONE",
                "regime": "unknown",
            }
        )

        try:
            total_rows = 0
            used_rows = 0
            skipped_no_pnl = 0
            skipped_flat_reason = 0
            skipped_near_zero = 0
            skipped_exchange_closed_unknown = 0
            min_abs_pnl = max(0.0, float(os.getenv("KILL_SWITCH_MIN_ABS_PNL", "0.001")))

            if position_ledger is not None:
                (
                    total_rows,
                    used_rows,
                    skipped_no_pnl,
                    skipped_flat_reason,
                    skipped_near_zero,
                    skipped_exchange_closed_unknown,
                ) = self._ingest_from_ledger(position_ledger, cutoff_ts, stats)
                logger.info(
                    "LOSER_KILL_SWITCH_INGEST source=ledger rows_total={} rows_used={} skipped_no_pnl={} skipped_flat_reason={} skipped_near_zero={} skipped_exchange_closed_unknown={} eps={} lookback_h={}",
                    total_rows,
                    used_rows,
                    skipped_no_pnl,
                    skipped_flat_reason,
                    skipped_near_zero,
                    skipped_exchange_closed_unknown,
                    min_abs_pnl,
                    self.lookback_hours,
                )

            if used_rows == 0:
                if not os.path.exists(self.db_path):
                    logger.warning("LOSER_KILL_SWITCH_DB_MISSING path={}", self.db_path)
                else:
                    (
                        total_rows,
                        used_rows,
                        skipped_no_pnl,
                        skipped_flat_reason,
                        skipped_near_zero,
                        skipped_exchange_closed_unknown,
                    ) = self._ingest_from_ai_logs(since_ms, stats)
                    logger.info(
                        "LOSER_KILL_SWITCH_INGEST source=ai_logs rows_total={} rows_used={} skipped_no_pnl={} skipped_flat_reason={} skipped_near_zero={} skipped_exchange_closed_unknown={} eps={} lookback_h={}",
                        total_rows,
                        used_rows,
                        skipped_no_pnl,
                        skipped_flat_reason,
                        skipped_near_zero,
                        skipped_exchange_closed_unknown,
                        min_abs_pnl,
                        self.lookback_hours,
                    )
        except Exception as exc:
            logger.warning("LOSER_KILL_SWITCH_REFRESH_FAILED err={}", exc)
            return 0

        new_blocks = 0
        for key, st in stats.items():
            n = int(st["n"])
            if n < self.min_trades:
                continue
            win_rate = float(st["wins"]) / n if n else 0.0
            gross_loss = float(st["gross_loss"])
            if gross_loss > 0:
                profit_factor = float(st["gross_profit"]) / gross_loss
            elif float(st["gross_profit"]) > 0:
                profit_factor = 999.0
            else:
                profit_factor = 0.0
            total_pnl = float(st["total_pnl"])
            has_loss_evidence = gross_loss > 0.0 or total_pnl < 0.0
            should_block = (
                has_loss_evidence
                and (
                    win_rate < self.min_win_rate
                    or profit_factor < self.min_profit_factor
                    or total_pnl <= self.max_total_pnl
                )
            )
            if should_block and key not in self.blocked_tuples:
                block_meta = {
                    "symbol": st["symbol"],
                    "entry_reason": st["entry_reason"],
                    "regime": st["regime"],
                    "n": n,
                    "win_rate": round(win_rate, 6),
                    "profit_factor": round(profit_factor, 6),
                    "total_pnl": round(total_pnl, 6),
                    "blocked_at_ms": int(now * 1000),
                }
                self.blocked_tuples[key] = block_meta
                new_blocks += 1
                logger.error(
                    "LOSER_TUPLE_BLOCKED tuple={} win_rate={:.1%} pf={:.2f} total_pnl={:.4f} n={}",
                    key,
                    win_rate,
                    profit_factor,
                    total_pnl,
                    n,
                )

        if new_blocks > 0:
            self._save_state()
        return new_blocks


# SDM Components
from .intent_graph import IntentGraph, Intent, IntentType
from .semantic_binding import SemanticBindingLayer, ModelType, MarketRegime
from .continuous_learning import ContinuousLearningEngine, PerformanceFeedback
from .constraint_propagation import ConstraintPropagator
from .ethics_engine import EthicsEngine
from .simple_momentum import SimpleMomentumStrategy

# AlphaGenesis Components
from alphagenesis.data import WEEXClient
from alphagenesis.features import (
    FeatureEngineer,
    MarketRegimeDetector as LegacyRegimeDetector,
    MultiTimeframeConfluence,
    TechnicalIndicators
)
from alphagenesis.features.market_regime import MarketRegimeDetector as RegimeDetectorV2, RegimeType
from alphagenesis.models import LSTMModel, TransformerModel, EnsemblePredictor
from alphagenesis.risk import RiskManager
from alphagenesis.risk.circuit_breaker import CircuitBreaker
from alphagenesis.risk.risk_manager_veto import RiskManagerVeto, AccountState, TradeIntent, VetoReason
from alphagenesis.execution.position_ledger import PositionLedger
from alphagenesis.execution.position_monitor import PositionMonitor
from alphagenesis.execution.breakout_straddle import BreakoutStraddleManager
from alphagenesis.learning import DecisionJournal, DecisionTick, TradeEvent, ContextualBanditAllocator
from alphagenesis.omni.ai_logs import AILogBus, AILogStore, AILogUploader, AILogWorker


class SDMTradingEngine:
    """
    Semantic Dataflow Machine Trading Engine.

    This engine continuously:
    - Resolves intent under constraints
    - Binds intent to optimal strategies
    - Propagates constraints as fields
    - Enforces ethics as asymmetric penalties
    - Learns and adapts from feedback
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        initial_capital: float = 1000.0,
        update_interval: int = 300,  # 5 minutes
    ):
        """
        Initialize SDM Trading Engine.

        Args:
            api_key: WEEX API key
            api_secret: WEEX API secret
            api_passphrase: WEEX API passphrase
            initial_capital: Starting capital in USDT
            update_interval: Seconds between iterations
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.legacy_amount = initial_capital
        self.update_interval = update_interval

        # Initialize WEEX client
        self.weex = WEEXClient(
            api_key=api_key or os.getenv('WEEX_API_KEY'),
            api_secret=api_secret or os.getenv('WEEX_API_SECRET'),
            api_passphrase=api_passphrase or os.getenv('WEEX_API_PASSPHRASE')
        )

        # AI log pipeline (non-blocking, persistent)
        self.ai_log_bus = None
        self.ai_log_worker = None
        if os.getenv("AI_LOG_ENABLED", "true").lower() == "true":
            try:
                db_path = os.getenv("AI_LOG_DB_PATH", "/opt/AlphaGenesis/tmp/ai_logs.sqlite")
                store = AILogStore(db_path)
                uploader = AILogUploader(self.weex)
                self.ai_log_bus = AILogBus(store)
                self.ai_log_bus = AILogBusWithExitSummary(self.ai_log_bus, self._record_exit_summary)
                self.ai_log_worker = AILogWorker(store, uploader)
                self.ai_log_worker.start()
            except Exception as e:
                logger.warning("AI log pipeline disabled due to init error: {}", e)

        # Initialize SDM Components
        logger.info("Initializing SDM Components...")

        # 1. Intent Graph - Defines WHAT we want
        self.intent_graph = IntentGraph()
        self.intent_graph.initialize_trading_intents()

        # 2. Semantic Binding Layer - Resolves HOW
        self.binding_layer = SemanticBindingLayer(embedding_dim=64)
        self._initialize_models()

        # 3. Constraint Propagator - Ensures SAFETY
        self.constraint_propagator = ConstraintPropagator()
        self.constraint_propagator.initialize_trading_constraints()

        # 4. Ethics Engine - Enforces PRINCIPLES
        self.ethics_engine = EthicsEngine()
        self.ethics_engine.initialize_trading_ethics()

        # 5. Continuous Learning - Ensures ADAPTATION
        self.learning_engine = ContinuousLearningEngine(
            learning_rate=0.01,
            adaptation_threshold=0.3,
            min_samples=10
        )

        # Legacy components for compatibility
        self.regime_detector = LegacyRegimeDetector()
        self.regime_detector_v2 = RegimeDetectorV2()
        self.confluence_analyzer = MultiTimeframeConfluence(timeframes=['1h', '4h', '1d'])
        self.technical = TechnicalIndicators()
        self.circuit_breaker = CircuitBreaker(
            max_leverage=20.0,
            max_daily_drawdown=0.10,
            max_total_drawdown=0.25
        )

        # Simple momentum strategy (proven indicators, not untrained ML)
        self.momentum_strategy = SimpleMomentumStrategy()
        logger.info("✓ Momentum strategy initialized (RSI, MA, momentum-based)")

        # CRITICAL: Position Ledger - Single Source of Truth for Conflict Prevention
        os.makedirs("/opt/AlphaGenesis/tmp", exist_ok=True)
        self.position_ledger = PositionLedger(ledger_path="/opt/AlphaGenesis/tmp/position_ledger.json")
        logger.info("✓ Position Ledger initialized - conflict prevention active")

        # PHASE 2: Risk Manager - Final Veto Authority
        tier_a_risk_pct = float(os.getenv("TIER_A_RISK_PCT", "0.025"))
        self.risk_manager = RiskManagerVeto(
            initial_balance=initial_capital,
            max_notional_per_symbol=2000.0,
            max_total_notional=5000.0,
            max_leverage=15.0,
            max_margin_ratio=0.80,
            max_daily_loss_pct=0.10,
            max_total_drawdown_pct=0.25,
            max_per_trade_risk_pct=tier_a_risk_pct,
            min_risk_reward_ratio=1.5,
            fee_churn_threshold=-0.01,
            fee_churn_lookback=10
        )
        logger.info("✓ Risk Manager initialized - final veto authority active")

        # PHASE 2: Decision Journal - Training Data Collection
        self.journal = DecisionJournal(db_path="/tmp/trading_journal.db")
        logger.info("✓ Decision Journal initialized - logging all decisions")

        # PHASE 2: Contextual Bandit - Online Strategy Selection
        self.bandit = ContextualBanditAllocator(
            strategies=['momentum', 'flat'],  # Start with 2, add more later
            algorithm='ucb',
            exploration_rate=0.2,
            ucb_c=2.0,
            state_path="/tmp/bandit_state.json"
        )
        logger.info("✓ Bandit Allocator initialized - online learning active")

        # PHASE 2: Position Monitor - Auto-Close Detection
        self.position_monitor = PositionMonitor(
            weex_client=self.weex,
            position_ledger=self.position_ledger,
            decision_journal=self.journal,
            bandit_allocator=self.bandit,
            poll_interval_seconds=30,
            ai_log_bus=self.ai_log_bus
        )
        logger.info("✓ Position Monitor initialized - will start with engine")

        # DRY RUN MODE
        self.dry_run_mode = os.getenv('DRY_RUN', 'false').lower() == 'true'
        if self.dry_run_mode:
            logger.warning("🟡 DRY RUN MODE ACTIVE - No real orders will be placed")

        # Diagnostic mode (suspend on 40753 without killing the engine)
        self.diagnostic_mode = os.getenv('DIAGNOSTIC_MODE', 'false').lower() == 'true'
        self.diagnostic_suspend_active = False
        self.diagnostic_suspend_since = 0.0
        self.diagnostic_last_log_ts = 0.0
        self.diagnostic_reason = None
        self._diag_blocked_in_fetch = False
        if self.diagnostic_mode:
            logger.warning("🟠 DIAGNOSTIC_MODE enabled - 40753 will suspend orders without stopping the engine")

        # Breakout straddle manager (hedge mode)
        self.straddle_manager = BreakoutStraddleManager(
            weex_client=self.weex,
            position_ledger=self.position_ledger,
            straddle_risk=0.18,
            breakout_pct=0.016,
            trail_activation_pct=0.01,
            trail_pct=0.006,
            initial_stop_loss_pct=0.01,
            max_hold_seconds=7200,
            cooldown_seconds=45,
            max_position_pct=0.25,
            dry_run=self.dry_run_mode,
            ai_log_bus=self.ai_log_bus
        )
        self.straddle_confidence_threshold = 0.55
        self._straddle_tick_seen = set()

        # State
        self.is_running = False
        self.positions: Dict[str, Any] = {}
        self.iteration = 0
        self._diag_gate_counts = {
            "normalized_no_signal": 0,
            "low_vol_block": 0,
            "has_signal_false": 0,
        }
        self._diag_block_counts = {
            "override_signals": 0,
            "opened_straddles": 0,
            "blocked_straddle_active": 0,
            "blocked_intent_veto": 0,
        }
        self._exit_summary = {
            "counts": {},
            "holds": [],
        }
        self._diag_gate_log_every = 10
        self.total_pnl = 0.0
        self.daily_trades = 0
        self.last_trade_time = None
        self.peak_balance_today = initial_capital
        self.daily_pnl = 0.0
        self.daily_pnl_percent = 0.0
        self._daily_date = datetime.now(timezone.utc).date().isoformat()
        self.daily_start_balance = initial_capital
        self.daily_pause_until = 0.0
        self.emergency_stop_active = False
        self.test_override_used = False
        self.start_time = time.time()
        self._equity_initialized = False
        self.btc_only_period = 0
        self.btc_base_balance = None
        self.gamma_squeeze_active = False
        unrealized_pnl, margin_used, total_notional = self._calculate_position_metrics(
            self.position_ledger.get_all_positions()
        )
        self._warned_pnl_field = False
        self._warned_leverage_field = False
        self.last_feedback_ts = 0.0
        self.feedback_interval_seconds = 4 * 60 * 60
        self.max_40015_errors = max(1, int(os.getenv("SYMBOL_40015_MAX_ERRORS", "3")))
        self.error40015_window_seconds = max(60, int(os.getenv("SYMBOL_40015_WINDOW_SECONDS", "600")))
        self.symbol_quarantine_seconds = max(60, int(os.getenv("SYMBOL_40015_QUARANTINE_SECONDS", "1800")))
        self.error_count_40015: Dict[str, List[float]] = defaultdict(list)
        self.quarantine_symbols: Dict[str, float] = {}
        self.bnb_tactical_quarantine_enabled = os.getenv("BNB_TACTICAL_QUARANTINE_ENABLED", "true").lower() == "true"
        self.bnb_tactical_symbol = self._normalize_symbol(os.getenv("BNB_TACTICAL_SYMBOL", "cmt_bnbusdt"))
        self.bnb_tactical_lookback_seconds = max(300, int(os.getenv("BNB_TACTICAL_LOOKBACK_SECONDS", "3600")))
        self.bnb_tactical_pnl_threshold = float(os.getenv("BNB_TACTICAL_PNL_THRESHOLD", "-1.5"))
        self.bnb_tactical_quarantine_seconds = max(300, int(os.getenv("BNB_TACTICAL_QUARANTINE_SECONDS", "3600")))
        self.bnb_tactical_check_interval_seconds = max(60, int(os.getenv("BNB_TACTICAL_CHECK_INTERVAL_SECONDS", "300")))
        self.bnb_tactical_quarantine_until = 0.0
        self.bnb_tactical_last_eval_ts = 0.0
        self.bnb_tactical_last_pnl = 0.0

        # Aggressive straddle controls (competition tuning)
        self.stop_new_if_pnl_under = -0.06
        self.emergency_stop_at = -0.08
        try:
            gross_cap_raw = float(os.getenv("MAX_GROSS_EXPOSURE_PCT", "0.30"))
        except (TypeError, ValueError):
            gross_cap_raw = 0.30
        self.max_gross_exposure_pct = max(0.05, min(1.0, gross_cap_raw))
        self.profit_lock_enabled = os.getenv("PROFIT_LOCK_ENABLED", "true").lower() == "true"
        try:
            profit_lock_trigger = float(os.getenv("PROFIT_LOCK_TRIGGER_PNL_PCT", "0.0025"))
        except (TypeError, ValueError):
            profit_lock_trigger = 0.0025
        self.profit_lock_trigger_pnl_pct = max(0.0, profit_lock_trigger)
        try:
            profit_lock_cap_raw = float(os.getenv("PROFIT_LOCK_GROSS_EXPOSURE_PCT", "0.20"))
        except (TypeError, ValueError):
            profit_lock_cap_raw = 0.20
        self.profit_lock_gross_exposure_pct = max(0.05, min(self.max_gross_exposure_pct, profit_lock_cap_raw))
        self._profit_lock_last_active: Optional[bool] = None

        # Symbol prioritization (tiered via env for finals)
        tier_a = os.getenv("TIER_A_PAIRS", "cmt_solusdt,cmt_ethusdt,cmt_ltcusdt").split(",")
        tier_b = os.getenv("TIER_B_PAIRS", "cmt_xrpusdt,cmt_bnbusdt,cmt_adausdt").split(",")
        tier_c = os.getenv("TIER_C_PAIRS", "cmt_dogeusdt,cmt_btcusdt").split(",")
        self.tier_a_pairs = [s.strip() for s in tier_a if s.strip()]
        self.tier_b_pairs = [s.strip() for s in tier_b if s.strip()]
        self.tier_c_pairs = [s.strip() for s in tier_c if s.strip()]

        self.tier_a_risk_pct = float(os.getenv("TIER_A_RISK_PCT", "0.025"))
        self.tier_b_risk_pct = float(os.getenv("TIER_B_RISK_PCT", "0.015"))
        self.tier_c_risk_pct = float(os.getenv("TIER_C_RISK_PCT", "0.01"))

        # Probe mode: controlled data collection with reduced size.
        self.probe_mode_enabled = os.getenv("PROBE_MODE_ENABLED", "true").lower() == "true"
        self.probe_entry_reason = os.getenv("PROBE_ENTRY_REASON", "LOW_VOL_EXTREME_OVERRIDE").strip()
        self.probe_override_allowlist = {
            s.strip().lower()
            for s in os.getenv("PROBE_OVERRIDE_ALLOWLIST", "cmt_solusdt,cmt_xrpusdt").split(",")
            if s.strip()
        }
        self.probe_size_multiplier = max(0.05, min(1.0, float(os.getenv("PROBE_SIZE_MULTIPLIER", "0.25"))))
        logger.info("PROBE_SIZE_MULTIPLIER_ACTIVE value={:.3f}", self.probe_size_multiplier)

        # Champion ladder scaling (tuple-only, data-gated).
        self.champion_ladder_enabled = os.getenv("CHAMPION_LADDER_ENABLED", "true").lower() == "true"
        self.champion_ladder_state_path = os.getenv("CHAMPION_LADDER_STATE_PATH", "/opt/AlphaGenesis/tmp/champion_ladder.json")
        self.champion_ladder_lookback_hours = max(1, int(os.getenv("CHAMPION_LADDER_LOOKBACK_HOURS", "48")))
        self.champion_ladder_degrade_hours = max(1, int(os.getenv("CHAMPION_LADDER_DEGRADE_HOURS", "12")))
        self.champion_ladder_quarantine_seconds = max(300, int(os.getenv("CHAMPION_LADDER_QUARANTINE_SECONDS", "7200")))
        self.champion_ladder_min_trades_promote = max(1, int(os.getenv("CHAMPION_LADDER_MIN_TRADES", "8")))
        self.champion_ladder_min_trades_revalidate = max(1, int(os.getenv("CHAMPION_LADDER_MIN_REVALIDATE_TRADES", "4")))
        self.champion_ladder_soft_quarantine_min_trades = max(1, int(os.getenv("CHAMPION_LADDER_SOFT_KILL_MIN_TRADES", "5")))
        self.champion_ladder_min_win_rate_promote = float(os.getenv("CHAMPION_LADDER_MIN_WIN_RATE", "0.55"))
        self.champion_ladder_min_profit_factor_promote = float(os.getenv("CHAMPION_LADDER_MIN_PROFIT_FACTOR", "1.60"))
        self.champion_ladder_min_net_pnl_promote = float(os.getenv("CHAMPION_LADDER_MIN_NET_PNL", "0.0"))
        self.champion_ladder_degrade_win_rate = float(os.getenv("CHAMPION_LADDER_DEGRADE_WIN_RATE", "0.45"))
        self.champion_ladder_degrade_profit_factor = float(os.getenv("CHAMPION_LADDER_DEGRADE_PROFIT_FACTOR", "1.0"))
        self.champion_ladder_degrade_net_pnl = float(os.getenv("CHAMPION_LADDER_DEGRADE_NET_PNL", "0.0"))
        self.champion_ladder_min_abs_pnl = max(
            0.0,
            float(os.getenv("CHAMPION_LADDER_MIN_ABS_PNL", os.getenv("KILL_SWITCH_MIN_ABS_PNL", "0.001"))),
        )
        self.tuple_decay_enabled = os.getenv("TUPLE_DECAY_ENABLED", "true").lower() == "true"
        try:
            tuple_decay_lambda = float(os.getenv("TUPLE_DECAY_LAMBDA", "0.95"))
        except (TypeError, ValueError):
            tuple_decay_lambda = 0.95
        self.tuple_decay_lambda = max(0.50, min(0.999, tuple_decay_lambda))
        self.champion_ladder_levels = (1.00, 1.10, 1.15)
        self.champion_ladder_state = self._load_champion_ladder_state()

        # Backward-compatible static champion tuple scaling (disabled by default).
        self.champion_tuple_enabled = os.getenv("CHAMPION_TUPLE_ENABLED", "false").lower() == "true"
        self.champion_symbol = os.getenv("CHAMPION_SYMBOL", "").strip().lower()
        self.champion_entry_reason = os.getenv("CHAMPION_ENTRY_REASON", "").strip()
        self.champion_regime = os.getenv("CHAMPION_REGIME", "").strip().lower()
        champion_size_raw = os.getenv("CHAMPION_SIZE_MULTIPLIER", "1.10")
        try:
            champion_size_parsed = float(champion_size_raw)
        except (TypeError, ValueError):
            champion_size_parsed = 1.10
        self.champion_size_multiplier = max(1.10, min(1.15, champion_size_parsed))
        self._champion_tuple_warned_incomplete = False

        # Stealth mode (deterministic jitter by tuple + 15m bucket).
        self.stealth_mode_enabled = os.getenv("STEALTH_MODE_ENABLED", "true").lower() == "true"
        self.stealth_time_jitter_ms_max = max(0, int(os.getenv("STEALTH_TIME_JITTER_MS_MAX", "450")))
        self.stealth_size_jitter_pct = max(0.0, min(0.25, float(os.getenv("STEALTH_SIZE_JITTER_PCT", "0.06"))))
        self.stealth_champion_extra_size_jitter_pct = max(
            0.0, min(0.10, float(os.getenv("STEALTH_CHAMPION_EXTRA_SIZE_JITTER_PCT", "0.02")))
        )
        self.stealth_seed_salt = os.getenv("STEALTH_SEED_SALT", "weex-finals")
        self.stealth_bucket_seconds = max(60, int(os.getenv("STEALTH_BUCKET_SECONDS", "900")))
        self.stealth_min_size_scale = max(0.01, float(os.getenv("STEALTH_MIN_SIZE_SCALE", "0.05")))
        self.stealth_max_size_scale = max(
            self.stealth_min_size_scale, float(os.getenv("STEALTH_MAX_SIZE_SCALE", "2.0"))
        )

        self.loser_kill_switch_enabled = os.getenv("LOSER_KILL_SWITCH_ENABLED", "true").lower() == "true"
        self.loser_kill_switch = LoserTupleKillSwitch(
            db_path=os.getenv("AI_LOG_DB_PATH", "/opt/AlphaGenesis/tmp/ai_logs.sqlite"),
            state_path=os.getenv("LOSER_TUPLE_BLOCKLIST_PATH", "/opt/AlphaGenesis/tmp/loser_tuple_blocklist.json"),
            lookback_hours=int(os.getenv("LOSER_TUPLE_LOOKBACK_HOURS", "24")),
            min_trades=int(os.getenv("LOSER_TUPLE_MIN_TRADES", "5")),
            min_win_rate=float(os.getenv("LOSER_TUPLE_MIN_WIN_RATE", "0.35")),
            min_profit_factor=float(os.getenv("LOSER_TUPLE_MIN_PROFIT_FACTOR", "0.80")),
            max_total_pnl=float(os.getenv("LOSER_TUPLE_MAX_TOTAL_PNL", "-20.0")),
            refresh_interval_seconds=int(os.getenv("LOSER_TUPLE_REFRESH_SECONDS", "300")),
        )
        if self.loser_kill_switch_enabled:
            seeded = self.loser_kill_switch.refresh(force=True, position_ledger=self.position_ledger)
            logger.warning(
                "LOSER_KILL_SWITCH_ACTIVE blocked_total={} new_blocks={}",
                self.loser_kill_switch.blocked_count(),
                seeded,
            )
        self._startup_champion_ladder_self_check()

        self.priority_symbols = list(self.tier_a_pairs)
        self.secondary_symbols = list(self.tier_b_pairs)
        self.max_active_symbols = 8
        self.symbols = self.tier_a_pairs + self.tier_b_pairs + self.tier_c_pairs
        self.active_symbols = list(self.symbols)
        if self.bnb_tactical_quarantine_enabled and self.bnb_tactical_symbol:
            logger.info(
                "BNB_TACTICAL_QUARANTINE_ENABLED symbol={} lookback_s={} threshold={} quarantine_s={}",
                self.bnb_tactical_symbol,
                self.bnb_tactical_lookback_seconds,
                self.bnb_tactical_pnl_threshold,
                self.bnb_tactical_quarantine_seconds,
            )
        if abs(self.champion_size_multiplier - champion_size_parsed) > 1e-9:
            logger.warning(
                "CHAMPION_SIZE_MULTIPLIER_CLAMPED raw={} clamped={:.3f}",
                champion_size_raw,
                self.champion_size_multiplier,
            )

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("="*70)
        logger.info("SDM TRADING ENGINE INITIALIZED")
        logger.info("="*70)
        logger.info("Intent Graph: Active with trading intents")
        logger.info("Semantic Binding: Model registry initialized")
        logger.info("Constraint Fields: Potential landscape configured")
        logger.info("Ethics Engine: First-class constraints enforced")
        logger.info("Learning Engine: Continuous adaptation enabled")
        logger.info("="*70)

    def _initialize_models(self):
        """Initialize and register models with binding layer."""
        # Register model types (simplified - actual models would be loaded)
        for model_type in ModelType:
            # Create placeholder model instances
            self.binding_layer.register_model(model_type, model_instance=None)

        logger.info("Models registered with semantic binding layer")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals cleanly."""
        signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
        logger.warning(f"Received {signal_name} ({signum}), initiating clean shutdown...")
        self.stop()
        # Force exit after stop completes
        import sys
        sys.exit(0)

    def _normalize_symbol(self, symbol: Optional[str]) -> str:
        return str(symbol or "").strip().lower()

    def _normalize_entry_reason(self, value: Any) -> str:
        reason = str(value or "").strip()
        return reason if reason else "LEGACY_NONE"

    def _normalize_entry_regime(self, value: Any) -> str:
        regime = str(value or "").strip().lower()
        return regime if regime else "unknown"

    def _tuple_key(self, symbol: Any, entry_reason: Any, regime: Any) -> str:
        return (
            f"{self._normalize_symbol(symbol) or 'unknown'}|"
            f"{self._normalize_entry_reason(entry_reason)}|"
            f"{self._normalize_entry_regime(regime)}"
        )

    def _split_tuple_key(self, tuple_key: str) -> tuple[str, str, str]:
        parts = str(tuple_key or "unknown|LEGACY_NONE|unknown").split("|", 2)
        while len(parts) < 3:
            parts.append("unknown")
        return parts[0], parts[1], parts[2]

    def _default_champion_tuple_state(self) -> Dict[str, Any]:
        return {
            "level": 1.00,
            "since_ms": 0,
            "n_at_level": 0,
            "last_eval_ms": 0,
            "quarantine_until_ms": 0,
        }

    def _load_champion_ladder_state(self) -> Dict[str, Any]:
        default_state = {"tuples": {}}
        path = os.getenv("CHAMPION_LADDER_STATE_PATH", "/opt/AlphaGenesis/tmp/champion_ladder.json")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                return default_state
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                return default_state
            tuples_data = data.get("tuples")
            if not isinstance(tuples_data, dict):
                return default_state
            normalized: Dict[str, Dict[str, Any]] = {}
            for key, state in tuples_data.items():
                if not isinstance(state, dict):
                    continue
                normalized_state = self._default_champion_tuple_state()
                try:
                    normalized_state["level"] = float(state.get("level", 1.0) or 1.0)
                except (TypeError, ValueError):
                    normalized_state["level"] = 1.0
                if normalized_state["level"] >= 1.149:
                    normalized_state["level"] = 1.15
                elif normalized_state["level"] >= 1.099:
                    normalized_state["level"] = 1.10
                else:
                    normalized_state["level"] = 1.00
                for field in ("since_ms", "n_at_level", "last_eval_ms", "quarantine_until_ms"):
                    try:
                        normalized_state[field] = int(state.get(field, normalized_state[field]) or 0)
                    except (TypeError, ValueError):
                        normalized_state[field] = 0
                normalized[str(key)] = normalized_state
            return {"tuples": normalized}
        except Exception as exc:
            logger.warning("CHAMPION_LADDER_STATE_LOAD_FAILED path={} err={}", path, exc)
            return default_state

    def _save_champion_ladder_state(self) -> None:
        path = self.champion_ladder_state_path
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = f"{path}.tmp"
            payload = {
                "updated_at_ms": int(time.time() * 1000),
                "tuples": self.champion_ladder_state.get("tuples", {}),
            }
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=True, separators=(",", ":"))
            os.replace(tmp_path, path)
        except Exception as exc:
            logger.warning("CHAMPION_LADDER_STATE_SAVE_FAILED path={} err={}", path, exc)

    def _get_champion_tuple_state(self, tuple_key: str) -> Dict[str, Any]:
        tuples_state = self.champion_ladder_state.setdefault("tuples", {})
        state = tuples_state.get(tuple_key)
        if not isinstance(state, dict):
            state = self._default_champion_tuple_state()
            tuples_state[tuple_key] = state
        else:
            state.setdefault("level", 1.00)
            state.setdefault("since_ms", 0)
            state.setdefault("n_at_level", 0)
            state.setdefault("last_eval_ms", 0)
            state.setdefault("quarantine_until_ms", 0)
        return state

    def _extract_net_realized_pnl(self, trade: Any) -> Optional[float]:
        if trade is None:
            return None
        getter = trade.get if isinstance(trade, dict) else lambda k, d=None: getattr(trade, k, d)
        pnl_value = getter("realized_pnl")
        if pnl_value is None:
            return None
        try:
            pnl_float = float(pnl_value)
        except (TypeError, ValueError):
            return None
        fees_estimated = getter("fees_estimated", 0.0)
        try:
            fees_float = float(fees_estimated or 0.0)
        except (TypeError, ValueError):
            fees_float = 0.0
        pnl_is_net = bool(getter("pnl_is_net", False))
        if not pnl_is_net:
            pnl_float -= fees_float
        return pnl_float

    def _should_skip_closed_trade(self, trade: Any, min_abs_pnl: float) -> tuple[bool, Optional[float]]:
        if trade is None:
            return True, None
        getter = trade.get if isinstance(trade, dict) else lambda k, d=None: getattr(trade, k, d)
        close_reason = str(getter("close_reason", "") or "").strip().lower()
        if close_reason == "exchange_flat_detected":
            return True, None
        reason_norm = self._normalize_entry_reason(getter("entry_reason")).lower()
        regime_norm = self._normalize_entry_regime(getter("entry_regime")).lower()
        if close_reason == "exchange_closed" and reason_norm in {"legacy_none", "unknown", "none"} and regime_norm in {"unknown", "none"}:
            return True, None
        pnl_float = self._extract_net_realized_pnl(trade)
        if pnl_float is None:
            return True, None
        if min_abs_pnl > 0.0 and abs(pnl_float) < min_abs_pnl:
            return True, None
        return False, pnl_float

    def _init_tuple_stats(self) -> Dict[str, Any]:
        return {
            "n": 0,
            "raw_n": 0,
            "wins": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_pnl": 0.0,
            "win_rate": 0.0,
            "pf": 0.0,
        }

    def _update_tuple_stats(self, stats: Dict[str, Any], pnl: float, weight: float = 1.0) -> None:
        trade_weight = max(0.0, float(weight or 0.0))
        if trade_weight <= 0.0:
            return
        stats["raw_n"] += 1
        stats["n"] += trade_weight
        stats["net_pnl"] += (pnl * trade_weight)
        if pnl > 0:
            stats["wins"] += trade_weight
            stats["gross_profit"] += (pnl * trade_weight)
        elif pnl < 0:
            stats["gross_loss"] += (abs(pnl) * trade_weight)

    def _finalize_tuple_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        n = float(stats.get("n", 0.0) or 0.0)
        wins = float(stats.get("wins", 0.0) or 0.0)
        gross_profit = float(stats.get("gross_profit", 0.0) or 0.0)
        gross_loss = float(stats.get("gross_loss", 0.0) or 0.0)
        if n > 0.0:
            win_rate = wins / n
        else:
            win_rate = 0.0
        if gross_loss > 0:
            pf = gross_profit / gross_loss
        elif gross_profit > 0:
            pf = 999.0
        else:
            pf = 0.0
        stats["win_rate"] = win_rate
        stats["pf"] = pf
        return stats

    def _collect_tuple_window_stats(
        self,
        symbol: str,
        entry_reason: str,
        regime: str,
        lookback_hours: int,
        degrade_hours: int,
        since_ms: int = 0,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        overall = self._init_tuple_stats()
        degrade = self._init_tuple_stats()
        at_level = self._init_tuple_stats()

        now_ms = int(time.time() * 1000)
        lookback_cutoff_ms = now_ms - (max(1, int(lookback_hours)) * 3600 * 1000)
        degrade_cutoff_ms = now_ms - (max(1, int(degrade_hours)) * 3600 * 1000)
        max_window_hours = max(lookback_hours, degrade_hours, 1)
        tuple_key = self._tuple_key(symbol, entry_reason, regime)

        try:
            trades = self.position_ledger.get_recent_closed_trades(hours=max_window_hours, limit=5000)
        except Exception as exc:
            logger.warning("CHAMPION_TUPLE_STATS_QUERY_FAILED tuple={} err={}", tuple_key, exc)
            return self._finalize_tuple_stats(overall), self._finalize_tuple_stats(degrade), self._finalize_tuple_stats(at_level)

        min_abs_pnl = self.champion_ladder_min_abs_pnl
        for trade in trades:
            skip, pnl_float = self._should_skip_closed_trade(trade, min_abs_pnl)
            if skip or pnl_float is None:
                continue
            getter = trade.get if isinstance(trade, dict) else lambda k, d=None: getattr(trade, k, d)
            trade_tuple_key = self._tuple_key(
                getter("symbol"),
                getter("entry_reason"),
                getter("entry_regime"),
            )
            if trade_tuple_key != tuple_key:
                continue
            try:
                close_ms = int(float(getter("close_time", 0.0) or 0.0) * 1000)
            except (TypeError, ValueError):
                close_ms = 0
            if close_ms <= 0:
                continue
            weight = 1.0
            if self.tuple_decay_enabled:
                age_hours = max(0.0, (now_ms - close_ms) / 3600000.0)
                weight = float(self.tuple_decay_lambda ** age_hours)
            if close_ms >= lookback_cutoff_ms:
                self._update_tuple_stats(overall, pnl_float, weight=weight)
            if close_ms >= degrade_cutoff_ms:
                self._update_tuple_stats(degrade, pnl_float, weight=weight)
            if since_ms > 0 and close_ms >= int(since_ms):
                self._update_tuple_stats(at_level, pnl_float, weight=weight)

        return (
            self._finalize_tuple_stats(overall),
            self._finalize_tuple_stats(degrade),
            self._finalize_tuple_stats(at_level),
        )

    def _champion_gate_met(self, stats: Dict[str, Any], min_trades: int) -> bool:
        n = int(stats.get("raw_n", 0) or 0)
        win_rate = float(stats.get("win_rate", 0.0) or 0.0)
        pf = float(stats.get("pf", 0.0) or 0.0)
        net_pnl = float(stats.get("net_pnl", 0.0) or 0.0)
        return (
            n >= max(1, int(min_trades))
            and (win_rate > self.champion_ladder_min_win_rate_promote or pf > self.champion_ladder_min_profit_factor_promote)
            and net_pnl > self.champion_ladder_min_net_pnl_promote
        )

    def _evaluate_champion_tuple(
        self,
        symbol: str,
        entry_reason: str,
        regime: str,
    ) -> Dict[str, Any]:
        tuple_key = self._tuple_key(symbol, entry_reason, regime)
        state = self._get_champion_tuple_state(tuple_key)
        prev_level = float(state.get("level", 1.0) or 1.0)
        prev_level = 1.15 if prev_level >= 1.149 else (1.10 if prev_level >= 1.099 else 1.00)
        now_ms = int(time.time() * 1000)
        decision = "hold"
        promoted = False
        changed = False
        quarantine_until_ms = int(state.get("quarantine_until_ms", 0) or 0)

        overall_stats, degrade_stats, at_level_stats = self._collect_tuple_window_stats(
            symbol=symbol,
            entry_reason=entry_reason,
            regime=regime,
            lookback_hours=self.champion_ladder_lookback_hours,
            degrade_hours=self.champion_ladder_degrade_hours,
            since_ms=int(state.get("since_ms", 0) or 0),
        )

        new_n_at_level = int(at_level_stats.get("raw_n", 0) or 0)
        if int(state.get("n_at_level", 0) or 0) != new_n_at_level:
            state["n_at_level"] = new_n_at_level
            changed = True
        state["last_eval_ms"] = now_ms

        if quarantine_until_ms > now_ms:
            decision = "quarantine_active"
            if float(state.get("level", 1.0) or 1.0) != 1.00:
                state["level"] = 1.00
                changed = True
        else:
            if quarantine_until_ms > 0:
                state["quarantine_until_ms"] = 0
                changed = True

            degraded = (
                prev_level > 1.00
                and int(degrade_stats.get("raw_n", 0) or 0) > 0
                and (
                    float(degrade_stats.get("pf", 0.0) or 0.0) < self.champion_ladder_degrade_profit_factor
                    or float(degrade_stats.get("win_rate", 0.0) or 0.0) < self.champion_ladder_degrade_win_rate
                    or float(degrade_stats.get("net_pnl", 0.0) or 0.0) < self.champion_ladder_degrade_net_pnl
                )
            )
            if degraded:
                state["level"] = 1.00
                state["since_ms"] = now_ms
                state["n_at_level"] = 0
                state["quarantine_until_ms"] = now_ms + (self.champion_ladder_quarantine_seconds * 1000)
                decision = "degraded_rollback"
                changed = True
                logger.warning(
                    "CHAMPION_DEGRADED_ROLLBACK tuple={} level_prev={:.2f} reason=pf:{:.3f}|wr:{:.3f}|net:{:.3f} quarantine_s={}",
                    tuple_key,
                    prev_level,
                    float(degrade_stats.get("pf", 0.0) or 0.0),
                    float(degrade_stats.get("win_rate", 0.0) or 0.0),
                    float(degrade_stats.get("net_pnl", 0.0) or 0.0),
                    self.champion_ladder_quarantine_seconds,
                )
            else:
                soft_quarantine = (
                    int(overall_stats.get("raw_n", 0) or 0) >= self.champion_ladder_soft_quarantine_min_trades
                    and float(overall_stats.get("net_pnl", 0.0) or 0.0) < 0.0
                )
                if soft_quarantine:
                    state["level"] = 1.00
                    state["since_ms"] = now_ms
                    state["n_at_level"] = 0
                    state["quarantine_until_ms"] = now_ms + (self.champion_ladder_quarantine_seconds * 1000)
                    decision = "soft_quarantine"
                    changed = True
                    logger.warning(
                        "CHAMPION_SOFT_QUARANTINE tuple={} n={} net_pnl={:.4f} quarantine_s={}",
                        tuple_key,
                        int(overall_stats.get("raw_n", 0) or 0),
                        float(overall_stats.get("net_pnl", 0.0) or 0.0),
                        self.champion_ladder_quarantine_seconds,
                    )
                else:
                    if prev_level <= 1.00 + 1e-9 and self._champion_gate_met(overall_stats, self.champion_ladder_min_trades_promote):
                        state["level"] = 1.10
                        state["since_ms"] = now_ms
                        state["n_at_level"] = 0
                        decision = "promoted_1.10"
                        promoted = True
                        changed = True
                        logger.info("CHAMPION_PROMOTED tuple={} from=1.00 to=1.10 reason=gate_met", tuple_key)
                    elif abs(prev_level - 1.10) <= 1e-9 and self._champion_gate_met(at_level_stats, self.champion_ladder_min_trades_revalidate):
                        state["level"] = 1.15
                        state["since_ms"] = now_ms
                        state["n_at_level"] = 0
                        decision = "promoted_1.15"
                        promoted = True
                        changed = True
                        logger.info("CHAMPION_PROMOTED tuple={} from=1.10 to=1.15 reason=revalidated", tuple_key)
                    else:
                        state["level"] = prev_level

        level = float(state.get("level", 1.0) or 1.0)
        if level >= 1.149:
            level = 1.15
        elif level >= 1.099:
            level = 1.10
        else:
            level = 1.00
        state["level"] = level

        if self.tuple_decay_enabled:
            logger.info(
                "TUPLE_DECAY_UPDATE tuple={} lam={:.3f} trades={:.3f} win_rate={:.3f} total_pnl={:.4f}",
                tuple_key,
                self.tuple_decay_lambda,
                float(overall_stats.get("n", 0.0) or 0.0),
                float(overall_stats.get("win_rate", 0.0) or 0.0),
                float(overall_stats.get("net_pnl", 0.0) or 0.0),
            )

        logger.info(
            "CHAMPION_EVAL tuple={} n={} win_rate={:.3f} pf={:.3f} net_pnl={:.4f} level={:.2f} decision={}",
            tuple_key,
            int(overall_stats.get("raw_n", 0) or 0),
            float(overall_stats.get("win_rate", 0.0) or 0.0),
            float(overall_stats.get("pf", 0.0) or 0.0),
            float(overall_stats.get("net_pnl", 0.0) or 0.0),
            level,
            decision,
        )

        if changed:
            self._save_champion_ladder_state()

        quarantine_active = int(state.get("quarantine_until_ms", 0) or 0) > now_ms
        return {
            "tuple_key": tuple_key,
            "level": level,
            "multiplier": level,
            "promoted": promoted,
            "decision": decision,
            "quarantine_active": quarantine_active,
            "quarantine_until_ms": int(state.get("quarantine_until_ms", 0) or 0),
            "n_at_level": int(state.get("n_at_level", 0) or 0),
        }

    def _startup_champion_ladder_self_check(self) -> None:
        tuples_state = self.champion_ladder_state.get("tuples", {})
        logger.info("CHAMPION_LADDER_LOADED tuples={}", len(tuples_state))
        if not self.champion_ladder_enabled:
            return

        # Evaluate tuples with at least 3 trades in the last 48h for startup visibility.
        stats_map: Dict[str, Dict[str, Any]] = {}
        try:
            trades = self.position_ledger.get_recent_closed_trades(hours=48, limit=5000)
        except Exception as exc:
            logger.warning("CHAMPION_LADDER_STARTUP_CHECK_FAILED err={}", exc)
            return

        for trade in trades:
            skip, pnl_float = self._should_skip_closed_trade(trade, self.champion_ladder_min_abs_pnl)
            if skip or pnl_float is None:
                continue
            getter = trade.get if isinstance(trade, dict) else lambda k, d=None: getattr(trade, k, d)
            key = self._tuple_key(
                getter("symbol"),
                getter("entry_reason"),
                getter("entry_regime"),
            )
            if key not in stats_map:
                stats_map[key] = self._init_tuple_stats()
            self._update_tuple_stats(stats_map[key], pnl_float)

        for tuple_key, stats in stats_map.items():
            finalized = self._finalize_tuple_stats(stats)
            if int(finalized.get("raw_n", 0) or 0) < 3:
                continue
            symbol, entry_reason, regime = self._split_tuple_key(tuple_key)
            self._evaluate_champion_tuple(symbol=symbol, entry_reason=entry_reason, regime=regime)

    def _get_stealth_profile(
        self,
        symbol: str,
        entry_reason: str,
        regime: str,
        champion_level: float,
    ) -> Dict[str, Any]:
        tuple_key = self._tuple_key(symbol, entry_reason, regime)
        now_ts = time.time()
        bucket = int(now_ts // self.stealth_bucket_seconds)
        seed_input = f"{self.stealth_seed_salt}|{tuple_key}|{bucket}"
        seed_hash = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
        seed_int = int(seed_hash[:16], 16)
        rng = random.Random(seed_int)
        time_jitter_ms = 0
        size_jitter_mult = 1.0
        jitter_pct = self.stealth_size_jitter_pct
        if champion_level > 1.0:
            jitter_pct += self.stealth_champion_extra_size_jitter_pct
        jitter_pct = max(0.0, min(0.35, jitter_pct))
        if self.stealth_mode_enabled:
            if self.stealth_time_jitter_ms_max > 0:
                time_jitter_ms = int(rng.uniform(0.0, float(self.stealth_time_jitter_ms_max)))
            if jitter_pct > 0.0:
                size_jitter_mult = 1.0 + rng.uniform(-jitter_pct, jitter_pct)
        return {
            "tuple_key": tuple_key,
            "bucket": bucket,
            "time_jitter_ms": time_jitter_ms,
            "size_jitter_mult": size_jitter_mult,
            "jitter_pct": jitter_pct,
        }

    def _cleanup_symbol_quarantine(self, now: Optional[float] = None) -> None:
        now_ts = now if now is not None else time.time()
        expired = [sym for sym, until in self.quarantine_symbols.items() if now_ts >= float(until)]
        for sym in expired:
            self.quarantine_symbols.pop(sym, None)
            self.error_count_40015.pop(sym, None)
            logger.info("SYMBOL_QUARANTINE_EXPIRED symbol={}", sym)

    def _get_symbol_quarantine_until(self, symbol: str) -> Optional[float]:
        sym = self._normalize_symbol(symbol)
        if not sym:
            return None
        return self.quarantine_symbols.get(sym)

    def _is_symbol_quarantined(self, symbol: str) -> bool:
        now_ts = time.time()
        self._cleanup_symbol_quarantine(now=now_ts)
        sym = self._normalize_symbol(symbol)
        if not sym:
            return False
        until = self.quarantine_symbols.get(sym)
        if until is None:
            return False
        if now_ts < float(until):
            logger.warning("SYMBOL_QUARANTINED_BLOCK symbol={} until={}", sym, int(float(until)))
            return True
        return False

    def _get_bnb_tactical_quarantine_until(self) -> float:
        return float(self.bnb_tactical_quarantine_until or 0.0)

    def _symbol_realized_pnl_lookback(self, symbol: str, lookback_seconds: int) -> tuple[float, int]:
        symbol_norm = self._normalize_symbol(symbol)
        if not symbol_norm:
            return 0.0, 0

        cutoff_ts = time.time() - max(60, int(lookback_seconds))
        lookback_hours = max(1, int((max(60, int(lookback_seconds)) + 3599) // 3600))
        pnl_sum = 0.0
        trades_count = 0

        try:
            recent = self.position_ledger.get_recent_closed_trades(hours=lookback_hours, limit=4000)
            for trade in recent:
                trade_symbol = self._normalize_symbol(getattr(trade, "symbol", None))
                if trade_symbol != symbol_norm:
                    continue
                try:
                    close_ts = float(getattr(trade, "close_time", 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                if close_ts < cutoff_ts:
                    continue
                close_reason = str(getattr(trade, "close_reason", "") or "").strip().lower()
                if close_reason == "exchange_flat_detected":
                    continue
                try:
                    pnl_val = float(getattr(trade, "realized_pnl", 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                pnl_sum += pnl_val
                trades_count += 1
        except Exception as exc:
            logger.warning("BNB_TACTICAL_PNL_QUERY_FAILED symbol={} err={}", symbol_norm, exc)

        return pnl_sum, trades_count

    def _evaluate_bnb_tactical_quarantine(self, force: bool = False) -> None:
        if not self.bnb_tactical_quarantine_enabled or not self.bnb_tactical_symbol:
            return

        now_ts = time.time()
        if self.bnb_tactical_quarantine_until and now_ts >= float(self.bnb_tactical_quarantine_until):
            self.bnb_tactical_quarantine_until = 0.0
            logger.info("BNB_TACTICAL_QUARANTINE_EXPIRED symbol={}", self.bnb_tactical_symbol)

        if not force and (now_ts - float(self.bnb_tactical_last_eval_ts or 0.0)) < self.bnb_tactical_check_interval_seconds:
            return

        self.bnb_tactical_last_eval_ts = now_ts
        pnl_sum, trades_count = self._symbol_realized_pnl_lookback(
            self.bnb_tactical_symbol,
            self.bnb_tactical_lookback_seconds,
        )
        self.bnb_tactical_last_pnl = pnl_sum
        if trades_count <= 0:
            return

        if pnl_sum <= self.bnb_tactical_pnl_threshold:
            new_until = now_ts + self.bnb_tactical_quarantine_seconds
            if new_until > float(self.bnb_tactical_quarantine_until or 0.0):
                self.bnb_tactical_quarantine_until = new_until
                logger.warning(
                    "BNB_TACTICAL_QUARANTINE_ACTIVATED symbol={} pnl_lookback={:.4f} trades={} lookback_s={} threshold={} until={}",
                    self.bnb_tactical_symbol,
                    pnl_sum,
                    trades_count,
                    self.bnb_tactical_lookback_seconds,
                    self.bnb_tactical_pnl_threshold,
                    int(new_until),
                )

    def _is_bnb_tactically_quarantined(self, symbol: str) -> bool:
        if not self.bnb_tactical_quarantine_enabled:
            return False
        symbol_norm = self._normalize_symbol(symbol)
        if not symbol_norm or symbol_norm != self.bnb_tactical_symbol:
            return False
        until_ts = float(self.bnb_tactical_quarantine_until or 0.0)
        now_ts = time.time()
        if until_ts <= 0 or now_ts >= until_ts:
            return False
        logger.warning(
            "BNB_TACTICAL_QUARANTINE_BLOCKED symbol={} until={} pnl_lookback={:.4f}",
            symbol_norm,
            int(until_ts),
            self.bnb_tactical_last_pnl,
        )
        return True

    def _register_40015_error(self, symbol: str, error_code: Any, error_msg: Any, source: str = "entry_order") -> bool:
        code_text = "" if error_code is None else str(error_code)
        msg_text = "" if error_msg is None else str(error_msg)
        combined = f"{code_text} {msg_text}".lower()
        if "40015" not in combined and "position side invalid" not in combined:
            return False

        now_ts = time.time()
        sym = self._normalize_symbol(symbol)
        if not sym:
            return True

        history = [ts for ts in self.error_count_40015.get(sym, []) if (now_ts - ts) <= self.error40015_window_seconds]
        history.append(now_ts)
        self.error_count_40015[sym] = history
        if len(history) >= self.max_40015_errors:
            until_ts = now_ts + self.symbol_quarantine_seconds
            previous_until = float(self.quarantine_symbols.get(sym, 0.0) or 0.0)
            if until_ts > previous_until:
                self.quarantine_symbols[sym] = until_ts
                logger.error(
                    "SYMBOL_QUARANTINE_ACTIVATED symbol={} until={} errors_in_window={} window_s={} reason=40015 source={}",
                    sym,
                    int(until_ts),
                    len(history),
                    self.error40015_window_seconds,
                    source,
                )
        return True

    def start(self):
        """Start the SDM trading engine."""
        logger.info("\n" + "="*70)
        logger.info("STARTING SDM TRADING ENGINE")
        logger.info("="*70)
        logger.info("Paradigm: Intent-Driven Semantic Dataflow")
        logger.info("Architecture: Post-Von Neumann Continuous Resolution")
        logger.info("Learning: Embodied in Dataflow")
        logger.info("="*70 + "\n")

        self.is_running = True

        # Start position monitor in background
        self.position_monitor.start()

        self._run_dataflow_loop()

    def stop(self):
        """Stop the SDM trading engine cleanly."""
        logger.info("Stopping SDM Trading Engine...")
        self.is_running = False

        try:
            # Stop position monitor
            if hasattr(self, 'position_monitor'):
                self.position_monitor.stop()
                logger.info("✓ Position monitor stopped")

            # Close journal database connection
            if hasattr(self, 'journal'):
                self.journal.close()
                logger.info("✓ Journal closed")

            # Export final results
            self._export_results()

            # Save final state
            if hasattr(self, 'position_ledger'):
                self.position_ledger._save(force=True)
                logger.info("✓ Ledger saved")

            if hasattr(self, 'bandit'):
                self.bandit._save_state()
                logger.info("✓ Bandit state saved")

            if self.ai_log_worker:
                self.ai_log_worker.stop()
                logger.info("✓ AI log worker stopped")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        logger.info("SDM Engine stopped cleanly.")

    def _run_dataflow_loop(self):
        """
        Main dataflow loop.

        This is NOT a control flow loop.
        This is continuous pressure resolution in meaning space.
        """
        while self.is_running:
            try:
                self.iteration += 1
                timestamp = datetime.now()
                self._cleanup_symbol_quarantine()
                self._evaluate_bnb_tactical_quarantine()

                if self.loser_kill_switch_enabled:
                    new_blocks = self.loser_kill_switch.refresh(position_ledger=self.position_ledger)
                    if new_blocks > 0:
                        logger.warning(
                            "LOSER_KILL_SWITCH_REFRESH new_blocks={} blocked_total={}",
                            new_blocks,
                            self.loser_kill_switch.blocked_count(),
                        )

                if self._diag_gate_log_every and self.iteration % self._diag_gate_log_every == 0:
                    counts = self._diag_gate_counts
                    logger.info(
                        "DIAG_GATE_COUNTS normalized_no_signal={} low_vol_block={} has_signal_false={}",
                        counts["normalized_no_signal"],
                        counts["low_vol_block"],
                        counts["has_signal_false"]
                    )
                    self._diag_gate_counts = {
                        "normalized_no_signal": 0,
                        "low_vol_block": 0,
                        "has_signal_false": 0,
                    }

                    block_counts = self._diag_block_counts
                    logger.info(
                        "DIAG_BLOCK_SUMMARY override_signals={} opened_straddles={} blocked_straddle_active={} blocked_intent_veto={}",
                        block_counts["override_signals"],
                        block_counts["opened_straddles"],
                        block_counts["blocked_straddle_active"],
                        block_counts["blocked_intent_veto"]
                    )
                    self._diag_block_counts = {
                        "override_signals": 0,
                        "opened_straddles": 0,
                        "blocked_straddle_active": 0,
                        "blocked_intent_veto": 0,
                    }

                    summary = self._consume_exit_summary()
                    if summary and summary.get("total", 0) > 0:
                        logger.info(
                            "DIAG_EXIT_SUMMARY total={} time_stop={} stop_loss={} take_profit={} runner={} breakout={} avg_hold_s={}",
                            summary.get("total", 0),
                            summary.get("time_stop", 0),
                            summary.get("stop_loss", 0),
                            summary.get("take_profit", 0),
                            summary.get("runner", 0),
                            summary.get("breakout", 0),
                            summary.get("avg_hold_s")
                        )

                logger.info(f"\n{'='*70}")
                logger.info(f"SDM ITERATION {self.iteration} - {timestamp}")
                logger.info(f"{'='*70}")

                # Step 1: Observe (Data arrives → Pressure increases)
                market_state = self._observe_market()

                # Step 2: Propagate Intent Graph (Activation propagates)
                self.intent_graph.step()

                # Step 3: Resolve Intent (Bind to execution)
                active_intents = self.intent_graph.get_most_active_intents(top_k=3)
                self._straddle_tick_seen = set()

                if (
                    self.dry_run_mode
                    and self.iteration > 5
                    and not self.test_override_used
                    and len(self.straddle_manager.active_symbols()) == 0
                ):
                    symbol = self.active_symbols[0] if self.active_symbols else "cmt_btcusdt"
                    try:
                        ticker = self.weex.get_ticker(symbol)
                        if 'data' in ticker:
                            price = float(ticker['data'].get('last', 0))
                        else:
                            price = float(ticker.get('last', 0))
                        if price > 0:
                            logger.warning("🔧 DEBUG: FORCING TEST STRADDLE IN DRY_RUN")
                            opened = self.straddle_manager.try_open(
                                symbol=symbol,
                                price=price,
                                legacy_amount=self.legacy_amount,
                                reason="DEBUG_DRY_RUN_TEST",
                                entry_side="BOTH",
                            )
                            if opened:
                                self.test_override_used = True
                                logger.info(f"✅ TEST STRADDLE TRIGGERED: {symbol} @ {price:.2f}")
                    except Exception as e:
                        logger.warning(f"Test straddle open failed for {symbol}: {e}")

                for intent_node in active_intents:
                    self._resolve_intent(intent_node, market_state)

                # Step 4: Continuous Rebinding (Check if bindings still optimal)
                self.binding_layer.continuous_rebinding()

                # Step 5: Adapt if necessary
                if self.learning_engine.should_adapt():
                    self.learning_engine.adapt(self.intent_graph, self.binding_layer)

                # Step 6: Reconcile position ledger (every 10 iterations)
                if self.iteration % 10 == 0:
                    ledger_ok = self._reconcile_position_ledger()
                    if not ledger_ok:
                        logger.critical("Ledger reconciliation failed - stopping trading")
                        break

                # Step 7: Log status
                self._log_sdm_status()
                self._maybe_run_feedback_loop()

                # Sleep until next iteration
                time.sleep(self.update_interval)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in dataflow loop: {e}", exc_info=True)
                time.sleep(60)

    def _extract_unrealized_pnl(self, pos: Dict[str, Any]) -> float:
        keys = [
            'unrealized_pnl',
            'unrealised_pnl',
            'unrealized_profit',
            'unrealised_profit',
            'unrealizedPnl',
            'unrealisedPnl',
            'unrealizedProfit',
            'upnl',
            'floating_profit',
            'floating_pl',
            'unrealizePnl',
        ]
        for key in keys:
            if key in pos and pos[key] is not None:
                try:
                    return float(pos[key])
                except (TypeError, ValueError):
                    continue

        if not self._warned_pnl_field:
            logger.warning(
                "⚠️ Could not find unrealized P&L field in position. Available keys: {}",
                list(pos.keys())
            )
            self._warned_pnl_field = True
        return 0.0

    def _extract_mark_price(self, pos: Dict[str, Any]) -> float:
        keys = [
            'mark_price',
            'markPrice',
            'fair_price',
            'fairPrice',
            'last_price',
            'last',
            'index_price',
            'open_price',
            'entry_price',
        ]
        for key in keys:
            if key in pos and pos[key] is not None:
                try:
                    price = float(pos[key])
                except (TypeError, ValueError):
                    continue
                if price > 0:
                    return price
        return 0.0

    def _extract_position_size(self, pos: Dict[str, Any]) -> float:
        for key in ('size', 'total', 'position', 'pos', 'qty'):
            if key in pos and pos[key] is not None:
                try:
                    return float(pos[key])
                except (TypeError, ValueError):
                    continue
        return 0.0

    def _extract_position_side(self, pos: Dict[str, Any]) -> str:
        side_value = pos.get('side')
        if side_value is None:
            side_value = pos.get('hold_side') or pos.get('holdSide')
        if isinstance(side_value, str):
            side_str = side_value.strip().lower()
            if 'long' in side_str or side_str == 'buy':
                return 'LONG'
            if 'short' in side_str or side_str == 'sell':
                return 'SHORT'
        if side_value is not None:
            try:
                side_num = int(side_value)
                return 'LONG' if side_num == 1 else 'SHORT'
            except (TypeError, ValueError):
                pass
        return ''

    def _normalize_positions(self, symbol: str, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for pos in positions:
            size = self._extract_position_size(pos)
            if size == 0:
                continue

            side_str = self._extract_position_side(pos)
            if not side_str and size < 0:
                side_str = 'SHORT'

            abs_size = abs(size)
            try:
                entry_price = float(
                    pos.get('open_price')
                    or pos.get('avg_open_price')
                    or pos.get('avgOpenPrice')
                    or pos.get('entry_price')
                    or pos.get('entryPrice')
                    or pos.get('avgPrice')
                    or pos.get('openPrice')
                    or 0
                )
            except (TypeError, ValueError):
                entry_price = 0.0
            if entry_price == 0.0:
                try:
                    open_value = float(pos.get('open_value', 0.0) or 0.0)
                except (TypeError, ValueError):
                    open_value = 0.0
                if open_value > 0 and abs_size > 0:
                    entry_price = open_value / abs_size

            mark_price = self._extract_mark_price(pos)
            unrealized_pnl = self._extract_unrealized_pnl(pos)

            try:
                notional = float(
                    pos.get('open_value')
                    or pos.get('position_value')
                    or pos.get('notional')
                    or pos.get('openValue')
                    or 0
                )
            except (TypeError, ValueError):
                notional = 0.0

            if notional == 0.0:
                ref_price = mark_price or entry_price
                if ref_price > 0:
                    notional = abs_size * ref_price

            try:
                leverage = float(pos.get('leverage') or pos.get('lever') or pos.get('leverage_rate') or 20)
            except (TypeError, ValueError):
                leverage = 20.0

            normalized.append({
                'symbol': pos.get('symbol') or symbol,
                'side': side_str or 'LONG',
                'size': abs_size,
                'entry_price': entry_price,
                'mark_price': mark_price,
                'open_value': notional,
                'leverage': leverage,
                'unrealized_pnl': unrealized_pnl,
            })
        return normalized

    def _fetch_positions(self) -> List[Dict[str, Any]]:
        positions: List[Dict[str, Any]] = []
        self._diag_blocked_in_fetch = False
        for symbol in self.symbols:
            try:
                response = self.weex.get_position(symbol)
            except Exception as e:
                logger.warning(f"Failed fetching position for {symbol}: {e}")
                continue
            if self._handle_weex_response(response, f"position:{symbol}"):
                self._diag_blocked_in_fetch = True
                continue

            if isinstance(response, dict) and isinstance(response.get('position'), list):
                data = response.get('position')
            else:
                data = response.get('data') if isinstance(response, dict) else response
            if isinstance(data, dict):
                for key in ('position', 'positions', 'data'):
                    if isinstance(data.get(key), list):
                        data = data.get(key)
                        break

            if not data:
                continue

            if isinstance(data, list):
                pos_list = data
            elif isinstance(data, dict):
                pos_list = [data]
            else:
                continue

            positions.extend(self._normalize_positions(symbol, pos_list))
        return positions

    def _get_response_code(self, response: Any) -> Optional[int]:
        if not isinstance(response, dict):
            return None
        for key in ("code", "status_code", "error_code"):
            value = response.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _get_response_message(self, response: Any) -> str:
        if not isinstance(response, dict):
            return ""
        for key in ("msg", "message", "error"):
            value = response.get(key)
            if value:
                return str(value)
        return ""

    def _handle_weex_response(self, response: Any, source: str) -> bool:
        code = self._get_response_code(response)
        if self.diagnostic_mode and code is not None:
            msg = self._get_response_message(response)
            if msg:
                msg = msg[:120]
            logger.info("🟠 DIAGNOSTIC_PARSE: source={}, code={}, msg={}", source, code, msg)
        if code == 40753:
            self._enter_diagnostic_suspend(source, response)
            return True
        return False

    def _enter_diagnostic_suspend(self, source: str, response: Any):
        if not self.diagnostic_mode:
            return
        if self.diagnostic_suspend_active:
            return
        reason = self._get_response_message(response) or "contract transaction business is disabled"
        self.diagnostic_suspend_active = True
        self.diagnostic_suspend_since = time.time()
        self.diagnostic_reason = f"{source}: {reason}"
        self.emergency_stop_active = False
        logger.critical(
            "🟠 DIAGNOSTIC_SUSPEND ACTIVE - 40753 futures permissions blocked ({}). Orders disabled.",
            self.diagnostic_reason
        )
        self._log_diagnostic_status(force=True)

    def _clear_diagnostic_suspend(self, source: str):
        if not self.diagnostic_suspend_active:
            return
        self.diagnostic_suspend_active = False
        self.diagnostic_reason = None
        logger.info("✅ DIAGNOSTIC_SUSPEND CLEARED - successful {} read", source)

    def _log_diagnostic_status(self, force: bool = False):
        if not self.diagnostic_suspend_active:
            return
        now = time.time()
        if force or (now - self.diagnostic_last_log_ts) >= 60:
            elapsed = int(now - self.diagnostic_suspend_since) if self.diagnostic_suspend_since else 0
            logger.warning(
                "🟠 DIAGNOSTIC_SUSPEND: waiting on WEEX futures permissions ({}), elapsed={}s",
                self.diagnostic_reason or "unknown",
                elapsed
            )
            self.diagnostic_last_log_ts = now

    def _calculate_position_metrics(self, positions: List[Dict[str, Any]]) -> tuple[float, float, float]:
        unrealized_pnl = 0.0
        margin_used = 0.0
        total_notional = 0.0

        if not positions:
            return unrealized_pnl, margin_used, total_notional

        if isinstance(positions, dict):
            positions = list(positions.values())

        for pos in positions:
            if isinstance(pos, str):
                continue

            if isinstance(pos, dict):
                getter = pos.get
            else:
                getter = lambda k, default=None: getattr(pos, k, default)

            try:
                size = float(getter('size', 0) or 0)
            except (TypeError, ValueError):
                size = 0.0
            if size == 0:
                continue

            unrealized_pnl += float(getter('unrealized_pnl', 0.0) or 0.0)

            try:
                notional = float(getter('open_value', 0) or 0)
            except (TypeError, ValueError):
                notional = 0.0

            if notional == 0.0:
                mark_price = float(getter('mark_price', 0) or 0)
                if mark_price > 0:
                    notional = abs(size) * mark_price

            total_notional += notional

            try:
                leverage = float(getter('leverage', 20) or 20)
            except (TypeError, ValueError):
                leverage = 20.0
            if leverage <= 0:
                if not self._warned_leverage_field:
                    logger.warning("⚠️ Invalid leverage on position; defaulting to 20x for margin calc")
                    self._warned_leverage_field = True
                leverage = 20.0
            margin_used += notional / leverage

        return unrealized_pnl, margin_used, total_notional

    def _extract_account_balances(
        self,
        account: Dict[str, Any],
        positions: List[Dict[str, Any]]
    ) -> tuple[float, float, float]:
        data = account.get('data', account)
        collateral = data.get('collateral') if isinstance(data, dict) else None
        if collateral is None and isinstance(account, dict):
            collateral = account.get('collateral')

        full_balance = 0.0
        contest_balance = 0.0
        if isinstance(collateral, list):
            for entry in collateral:
                if entry.get('coin_id') == 2:
                    try:
                        full_balance = float(entry.get('amount', 0) or 0)
                    except (TypeError, ValueError):
                        full_balance = 0.0
                    try:
                        contest_balance = float(entry.get('legacy_amount', 0) or 0)
                    except (TypeError, ValueError):
                        contest_balance = 0.0
                    break

        _, margin_used, _ = self._calculate_position_metrics(positions)
        if contest_balance <= 0:
            contest_balance = full_balance

        available_balance = contest_balance - margin_used

        return contest_balance, max(0.0, available_balance), full_balance

    def _update_risk_exposure_from_positions(self, positions: List[Dict[str, Any]]):
        for pos in positions:
            symbol = pos.get('symbol')
            if not symbol:
                continue
            notional = float(pos.get('open_value', 0.0) or 0.0)
            self.risk_manager.update_symbol_exposure(symbol, notional)

    def _can_open_position(self, symbol: str, new_side: str) -> tuple[bool, str]:
        """
        Block opening a position opposite an existing one.

        Returns (allowed, reason).
        """
        existing_pos = self.position_ledger.get_position(symbol)
        existing_side = existing_pos.side.upper() if existing_pos else 'FLAT'
        new_side = new_side.upper()

        if existing_side in ('LONG', 'SHORT') and existing_side != new_side:
            reason = (
                f"blocked_opposing_trade: existing={existing_pos.side} size={existing_pos.size}, "
                f"attempted={new_side}"
            )
            logger.warning(
                "🚨 BLOCKED OPPOSING TRADE: {} | Existing: {} (Size: {}) | Attempted: {}",
                symbol,
                existing_pos.side,
                existing_pos.size,
                new_side
            )
            return False, reason

        return True, "OK"

    def _augment_action_with_risk_metrics(self, action: Dict[str, Any]):
        trade_notional = action.get('position_size', 0.0) * action.get('entry_price', 0.0)
        position_concentration = (
            trade_notional / self.current_capital if self.current_capital > 0 else 0.0
        )
        total_drawdown = (
            (self.initial_capital - self.current_capital) / self.initial_capital
            if self.initial_capital > 0 else 0.0
        )
        action.update({
            'daily_drawdown': max(0.0, -self.daily_pnl_percent),
            'total_drawdown': max(0.0, total_drawdown),
            'position_concentration': max(0.0, position_concentration),
            'daily_trade_count': float(self.daily_trades),
            'open_position_count': float(len(self.position_ledger.get_all_positions())),
        })

    def _record_exit_summary(self, reason: str, age_s: Optional[float]) -> None:
        try:
            counts = self._exit_summary["counts"]
            counts[reason] = counts.get(reason, 0) + 1
            if age_s is not None:
                self._exit_summary["holds"].append(int(age_s))
        except Exception:
            pass

    def _consume_exit_summary(self) -> Dict[str, Any]:
        counts = self._exit_summary.get("counts", {})
        holds = self._exit_summary.get("holds", [])
        total = sum(counts.values())
        avg_hold_s = None
        if holds:
            avg_hold_s = int(sum(holds) / len(holds))
        summary = {
            "total": total,
            "time_stop": sum(v for k, v in counts.items() if "TIME_STOP" in k),
            "stop_loss": sum(v for k, v in counts.items() if "STOP_LOSS" in k),
            "take_profit": sum(v for k, v in counts.items() if "TAKE_PROFIT" in k),
            "runner": sum(v for k, v in counts.items() if "RUNNER" in k),
            "breakout": sum(v for k, v in counts.items() if "BREAKOUT" in k),
            "avg_hold_s": avg_hold_s,
        }
        self._exit_summary = {
            "counts": {},
            "holds": [],
        }
        return summary

    def _track_gate_counts(self, signal: Any, regime: MarketRegime):
        if not hasattr(self, "_diag_gate_counts"):
            return
        if not signal:
            self._diag_gate_counts["has_signal_false"] += 1
            return
        if isinstance(signal, str):
            self._diag_gate_counts["normalized_no_signal"] += 1
            if regime == MarketRegime.LOW_VOLATILITY:
                self._diag_gate_counts["low_vol_block"] += 1

    def _sanitize_meta(self, payload: Any) -> Any:
        try:
            import numpy as np
        except Exception:
            np = None
        if payload is None:
            return None
        if isinstance(payload, (str, int, float, bool)):
            return payload
        if np is not None:
            if isinstance(payload, np.generic):
                try:
                    return payload.item()
                except Exception:
                    return str(payload)
            if isinstance(payload, np.ndarray):
                return [self._sanitize_meta(x) for x in payload.tolist()]
        if isinstance(payload, dict):
            return {str(k): self._sanitize_meta(v) for k, v in payload.items()}
        if isinstance(payload, (list, tuple, set)):
            return [self._sanitize_meta(v) for v in payload]
        try:
            return str(payload)
        except Exception:
            return repr(payload)

    def _emit_ai_log(self, stage: str, model: str, input_payload: Dict[str, Any], output_payload: Dict[str, Any], explanation: str, order_id: Optional[str] = None):
        if not self.ai_log_bus:
            return
        try:
            # Ensure every AI log contains concise reasoning details
            ctx = {
                "symbol": input_payload.get("symbol"),
                "regime": input_payload.get("regime"),
                "strategy": input_payload.get("strategy"),
                "state": input_payload.get("state"),
                "reason": input_payload.get("reason") or output_payload.get("reason"),
                "direction": output_payload.get("direction"),
                "confidence": output_payload.get("confidence"),
                "entry_price": output_payload.get("entry_price"),
                "position_size": output_payload.get("position_size"),
                "stop_loss": output_payload.get("stop_loss"),
                "take_profit": output_payload.get("take_profit"),
            }
            ctx_str = " ".join(f"{k}={v}" for k, v in ctx.items() if v is not None)
            if not explanation or len(str(explanation).strip()) < 5:
                explanation = f"{stage}: {model} {ctx_str}"
            else:
                explanation = f"{explanation} | {ctx_str}"
            explanation = explanation[:1000]
            self.ai_log_bus.emit(
                stage=stage,
                model=model,
                input_payload=input_payload,
                output_payload=output_payload,
                explanation=explanation,
                order_id=order_id
            )
            if stage == "Decision Making":
                logger.info("AI_ENTRY_LOG_DETAILS stage={} model={} explanation={}", stage, model, explanation)
        except Exception as e:
            logger.warning("AI log emit failed: {}", e)

    def _observe_market(self) -> Dict[str, Any]:
        """
        Observe market state.

        Data arrival creates pressure in the system.
        """
        market_state = {
            'timestamp': datetime.now(),
            'symbols': {},
            'account': {}
        }

        # Get account state
        try:
            account = self.weex.get_account()
            if self._handle_weex_response(account, "account"):
                if self.diagnostic_mode:
                    self._log_diagnostic_status()
                    market_state['account'] = {
                        'balance': self.current_capital,
                        'diagnostic_suspend': True
                    }
                    return market_state
            positions = self._fetch_positions()
            if self.diagnostic_mode and self.diagnostic_suspend_active and self._diag_blocked_in_fetch:
                self._log_diagnostic_status()
                market_state['account'] = {
                    'balance': self.current_capital,
                    'diagnostic_suspend': True
                }
                return market_state
            if self.diagnostic_mode and self.diagnostic_suspend_active:
                self._clear_diagnostic_suspend("account/positions")
            unrealized_pnl, margin_used, total_notional = self._calculate_position_metrics(positions)
            total_balance, available_balance, full_balance = self._extract_account_balances(
                account,
                positions
            )
            logger.info(
                "Balances - Full: ${:.2f}, Contest: ${:.2f}, Available: ${:.2f}",
                full_balance,
                total_balance,
                available_balance
            )
            equity = total_balance + unrealized_pnl
            market_state['account'] = {
                'balance': available_balance,
                'total_balance': total_balance,
                'full_balance': full_balance,
                'equity': equity,
                'unrealized_pnl': unrealized_pnl,
                'margin_used': margin_used,
                'total_notional': total_notional,
                'daily_pnl': self.daily_pnl,
                'daily_pnl_percent': self.daily_pnl_percent,
                'pnl': equity - self.initial_capital
            }
            self.current_capital = equity
            self.legacy_amount = available_balance

            if not self._equity_initialized and equity > 0:
                self._equity_initialized = True
                self._daily_date = datetime.now(timezone.utc).date().isoformat()
                self.initial_capital = equity
                self.daily_start_balance = equity
                self.daily_pnl = 0.0
                self.daily_pnl_percent = 0.0
                self.daily_pause_until = 0.0
                self.emergency_stop_active = False
                self.peak_balance_today = equity
                if hasattr(self.risk_manager, "initial_balance"):
                    self.risk_manager.initial_balance = equity

            today = datetime.now(timezone.utc).date().isoformat()
            if today != self._daily_date:
                self._daily_date = today
                self.daily_start_balance = equity
                self.daily_pnl = 0.0
                self.daily_pnl_percent = 0.0
                self.daily_pause_until = 0.0
                self.emergency_stop_active = False
            else:
                self.daily_pnl = equity - self.daily_start_balance
                self.daily_pnl_percent = (
                    self.daily_pnl / self.daily_start_balance
                    if self.daily_start_balance > 0 else 0.0
                )
            self.peak_balance_today = max(self.peak_balance_today, equity)
            self.last_margin_used = margin_used
            self.last_unrealized_pnl = unrealized_pnl
            self.last_total_notional = total_notional
            if hasattr(self, "straddle_manager"):
                self.straddle_manager.set_daily_pnl(self.daily_pnl_percent)
            self._update_risk_exposure_from_positions(positions)
            self._update_symbol_selection(available_balance)
            self._update_gamma_mode()
        except Exception as e:
            logger.error(f"Error fetching account: {e}")
            market_state['account'] = {'balance': self.current_capital}

        # Update constraint propagator state
        self.constraint_propagator.update_state({
            'current_capital': self.current_capital,
            'total_drawdown': max(0, (self.initial_capital - self.current_capital) / self.initial_capital),
            'daily_trades': self.daily_trades,
            'position_count': len(self.positions)
        })

        return market_state

    def _resolve_intent(self, intent_node, market_state: Dict):
        """
        Resolve an intent to execution.

        This is where Intent becomes Action through Semantic Binding.
        """
        intent_id = intent_node.node_id
        intent = intent_node.intent

        logger.info(f"\n--- Resolving Intent: {intent.goal} ---")
        logger.info(f"Activation: {intent_node.activation_level:.2f}, Priority: {intent.priority:.1f}")

        now = time.time()
        if self.diagnostic_suspend_active:
            self._log_diagnostic_status()
            logger.warning("🟠 DIAGNOSTIC_SUSPEND - skipping intent resolution")
            return
        if self.emergency_stop_active:
            logger.critical("❌ EMERGENCY STOP ACTIVE - blocking all new actions")
            return

        if self.daily_pnl_percent <= self.emergency_stop_at:
            logger.critical("❌ DAILY DRAWDOWN LIMIT HIT - STOPPING ALL STRATEGIES")
            self.emergency_stop_active = True
            self._close_all_positions()
            return

        if self.daily_pnl_percent <= self.stop_new_if_pnl_under:
            if now >= self.daily_pause_until:
                self.daily_pause_until = now + (4 * 60 * 60)
                logger.warning("⚠ DAILY LOSS PAUSE - blocking new entries for 4h")
            if now < self.daily_pause_until:
                return

        # For each symbol, try to resolve intent
        if self.active_symbols:
            symbols_to_trade = [sym for sym in self.active_symbols if sym in self.symbols]
        else:
            ordered_symbols = []
            for sym in self.priority_symbols:
                if sym in self.symbols and sym not in ordered_symbols:
                    ordered_symbols.append(sym)
            for sym in self.secondary_symbols:
                if sym in self.symbols and sym not in ordered_symbols:
                    ordered_symbols.append(sym)
            for sym in self.symbols:
                if sym not in ordered_symbols:
                    ordered_symbols.append(sym)

            symbols_to_trade = ordered_symbols[:max(1, self.max_active_symbols)]

        logger.info(
            "DIAG_LOOP_ENTER symbols_count={} symbols={}",
            len(symbols_to_trade),
            symbols_to_trade
        )

        for symbol in symbols_to_trade:
            try:
                if symbol not in self._straddle_tick_seen:
                    try:
                        ticker = self.weex.get_ticker(symbol)
                        if 'data' in ticker:
                            price = float(ticker['data'].get('last', 0))
                        else:
                            price = float(ticker.get('last', 0))
                        if price > 0:
                            logger.info("DIAG_STRADDLE_UPDATE_CALL symbol={} price={}", symbol, price)
                            self.straddle_manager.update(symbol, price)
                    except Exception as e:
                        logger.warning(f"Straddle update failed for {symbol}: {e}")
                    self._straddle_tick_seen.add(symbol)


                blocked = self.straddle_manager.is_blocked(symbol)

                logger.info("DIAG_STRADDLE_BLOCK_CHECK symbol={} blocked={}", symbol, blocked)
                try:
                    _st = self.straddle_manager._get_state(symbol)
                    _st_state = _st.get("state") if isinstance(_st, dict) else None
                    if _st_state not in {"IDLE", "DONE"}:
                        logger.info("DIAG_STRADDLE_STATE symbol={} state={} entry_time={} cooldown_until={}",
                                    symbol, _st_state, _st.get("entry_time"), _st.get("cooldown_until"))
                except Exception as _e:
                    logger.info("DIAG_STRADDLE_STATE symbol={} state=ERROR err={}", symbol, _e)

                if blocked:
                    logger.info("DIAG_LOOP_SKIP symbol={} reason=straddle_blocked", symbol)
                    logger.info(f"⏸ STRADDLE ACTIVE - skipping normal strategy for {symbol}")
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": None,
                            "signal": None,
                            "confidence": 0.0,
                            "straddle_active": True,
                            "open_positions": open_positions,
                            "capital": capital,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "STRADDLE_BLOCKED",
                        },
                        explanation=(
                            "HOLD: regime=None, confidence=0.0, straddle_active=True, "
                            f"open_positions={open_positions}, capital=${capital:.2f}, "
                            "reason=STRADDLE_BLOCKED"
                        ),
                    )
                    continue

                if self._is_symbol_quarantined(symbol):
                    quarantine_until = self._get_symbol_quarantine_until(symbol)
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    logger.info(
                        "DIAG_LOOP_SKIP symbol={} reason=symbol_quarantined until={}",
                        symbol,
                        int(float(quarantine_until or 0.0)),
                    )
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": None,
                            "signal": None,
                            "confidence": 0.0,
                            "symbol_quarantined": True,
                            "quarantine_until": quarantine_until,
                            "open_positions": open_positions,
                            "capital": capital,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "SYMBOL_QUARANTINED",
                        },
                        explanation=(
                            "HOLD: symbol_quarantined=True, "
                            f"quarantine_until={int(float(quarantine_until or 0.0))}, "
                            f"open_positions={open_positions}, capital=${capital:.2f}, "
                            "reason=SYMBOL_QUARANTINED"
                        ),
                    )
                    continue

                if self._is_bnb_tactically_quarantined(symbol):
                    quarantine_until = self._get_bnb_tactical_quarantine_until()
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    logger.info(
                        "DIAG_LOOP_SKIP symbol={} reason=bnb_tactical_quarantined until={}",
                        symbol,
                        int(float(quarantine_until or 0.0)),
                    )
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": None,
                            "signal": None,
                            "confidence": 0.0,
                            "bnb_tactical_quarantined": True,
                            "bnb_quarantine_until": quarantine_until,
                            "bnb_pnl_lookback": self.bnb_tactical_last_pnl,
                            "open_positions": open_positions,
                            "capital": capital,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "BNB_TACTICAL_QUARANTINED",
                        },
                        explanation=(
                            "HOLD: bnb_tactical_quarantined=True, "
                            f"quarantine_until={int(float(quarantine_until or 0.0))}, "
                            f"bnb_pnl_lookback={self.bnb_tactical_last_pnl:.4f}, "
                            f"open_positions={open_positions}, capital=${capital:.2f}, "
                            "reason=BNB_TACTICAL_QUARANTINED"
                        ),
                    )
                    continue

                # Determine market regime
                regime = self._detect_regime_for_symbol(symbol)

                # Bind intent to model via semantic binding
                account_state = market_state.get('account')
                if not isinstance(account_state, dict):
                    logger.error(
                        "BAD_ACCOUNT_STATE symbol={} type={} value={}",
                        symbol,
                        type(account_state).__name__,
                        account_state
                    )
                    account_state = {'balance': self.current_capital}
                context = {
                    'regime': regime,
                    'symbol': symbol,
                    'balance': account_state.get('balance', self.current_capital)
                }

                best_model = self.binding_layer.get_best_model_for_context(intent_id, context)

                if not best_model:
                    logger.debug(f"No suitable model binding for {intent_id} in {regime.value}")
                    continue

                logger.info(f"Bound {intent_id} -> {best_model.value} for {symbol} in {regime.value}")

                # Generate proposed action
                proposed_action = self._generate_action(
                    symbol=symbol,
                    model_type=best_model,
                    regime=regime,
                    intent=intent,
                    context=context
                )

                logger.info(
                    "PROPOSED_ACTION_RAW symbol={} type={} value={}",
                    symbol,
                    type(proposed_action).__name__,
                    proposed_action
                )
                if not isinstance(proposed_action, dict):
                    logger.error(
                        "BAD_PROPOSED_ACTION_TYPE symbol={} type={} value={}",
                        symbol,
                        type(proposed_action).__name__,
                        proposed_action
                    )
                    if isinstance(proposed_action, str):
                        proposed_action = {
                            "direction": "HOLD",
                            "confidence": 0.0,
                            "reason": proposed_action,
                        }
                    else:
                        continue

                if not proposed_action or proposed_action.get('direction') == 'HOLD':
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    regime_str = regime.value if hasattr(regime, "value") else str(regime)
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": regime_str,
                            "signal": None,
                            "confidence": 0.0,
                            "straddle_active": False,
                            "open_positions": open_positions,
                            "capital": capital,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "NO_SIGNAL",
                        },
                        explanation=(
                            "HOLD: regime={regime}, confidence=0.0, straddle_active=False, "
                            "open_positions={open_positions}, capital=${capital:.2f}, "
                            "reason=NO_SIGNAL"
                        ).format(
                            regime=regime_str,
                            open_positions=open_positions,
                            capital=capital,
                        ),
                    )
                    continue

                action_reason = proposed_action.get("reason")
                if not action_reason and isinstance(proposed_action.get("entry_meta"), dict):
                    action_reason = proposed_action.get("entry_meta", {}).get("entry_reason")
                if not action_reason:
                    action_reason = "LEGACY_NONE"
                action_regime = proposed_action.get("regime")
                if not action_regime:
                    action_regime = regime.value if hasattr(regime, "value") else str(regime)

                if self.loser_kill_switch_enabled and self.loser_kill_switch.is_blocked(symbol, action_reason, action_regime):
                    block_meta = self.loser_kill_switch.get_block_meta(symbol, action_reason, action_regime)
                    logger.error(
                        "LOSER_TUPLE_BLOCKED_TRADE symbol={} entry_reason={} regime={} n={} win_rate={} pf={} total_pnl={}",
                        symbol,
                        action_reason,
                        action_regime,
                        block_meta.get("n"),
                        block_meta.get("win_rate"),
                        block_meta.get("profit_factor"),
                        block_meta.get("total_pnl"),
                    )
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": action_regime,
                            "signal": action_reason,
                            "entry_reason": action_reason,
                            "confidence": proposed_action.get("confidence", 0.0),
                            "straddle_active": False,
                            "open_positions": open_positions,
                            "capital": capital,
                            "kill_switch": True,
                            "kill_switch_meta": block_meta,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "LOSER_TUPLE_BLOCKED",
                            "kill_switch_meta": block_meta,
                        },
                        explanation=(
                            "HOLD: reason=LOSER_TUPLE_BLOCKED tuple={symbol}|{entry_reason}|{regime} "
                            "metrics={meta}"
                        ).format(
                            symbol=symbol,
                            entry_reason=action_reason,
                            regime=action_regime,
                            meta=block_meta,
                        ),
                    )
                    continue

                champion_quarantine_until_ms = int(proposed_action.get("champion_quarantine_until_ms", 0) or 0)
                if bool(proposed_action.get("champion_quarantined")):
                    block_meta = {
                        "tuple_key": proposed_action.get("champion_tuple_key"),
                        "level": proposed_action.get("champion_level", 1.0),
                        "quarantine_until_ms": champion_quarantine_until_ms,
                    }
                    logger.warning(
                        "CHAMPION_QUARANTINE_BLOCK symbol={} entry_reason={} regime={} tuple={} until_ms={}",
                        symbol,
                        action_reason,
                        action_regime,
                        proposed_action.get("champion_tuple_key"),
                        champion_quarantine_until_ms,
                    )
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": action_regime,
                            "signal": action_reason,
                            "entry_reason": action_reason,
                            "confidence": proposed_action.get("confidence", 0.0),
                            "straddle_active": False,
                            "open_positions": open_positions,
                            "capital": capital,
                            "champion_quarantine": True,
                            "champion_meta": block_meta,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "CHAMPION_TUPLE_QUARANTINED",
                            "champion_meta": block_meta,
                        },
                        explanation=(
                            "HOLD: reason=CHAMPION_TUPLE_QUARANTINED tuple={tuple_key} until_ms={until_ms}"
                        ).format(
                            tuple_key=block_meta["tuple_key"],
                            until_ms=champion_quarantine_until_ms,
                        ),
                    )
                    continue

                self._augment_action_with_risk_metrics(proposed_action)

                # Evaluate action against intent graph
                should_execute, reasoning = self.intent_graph.should_execute_action(proposed_action)

                if not should_execute:
                    logger.info(f"Intent graph rejected: {reasoning}")
                    self._diag_block_counts["blocked_intent_veto"] += 1
                    self._log_straddle_signal_debug(
                        symbol=symbol,
                        action=proposed_action,
                        intent_graph_blocked=True
                    )
                    open_positions = len(self.position_ledger.get_all_positions())
                    capital = self.current_capital
                    regime_str = proposed_action.get("regime")
                    conf = proposed_action.get("confidence", 0.0)
                    self._emit_ai_log(
                        stage="Decision Making",
                        model="AlphaGenesis-SDM-v1",
                        input_payload={
                            "symbol": symbol,
                            "regime": regime_str,
                            "signal": proposed_action.get("reason"),
                            "confidence": conf,
                            "straddle_active": False,
                            "open_positions": open_positions,
                            "capital": capital,
                        },
                        output_payload={
                            "action": "HOLD",
                            "reason": "INTENT_GRAPH_REJECTED",
                        },
                        explanation=(
                            "HOLD: regime={regime}, confidence={conf}, straddle_active=False, "
                            "open_positions={open_positions}, capital=${capital:.2f}, "
                            "reason=INTENT_GRAPH_REJECTED"
                        ).format(
                            regime=regime_str,
                            conf=conf,
                            open_positions=open_positions,
                            capital=capital,
                        ),
                    )
                    continue

                # Apply constraint propagation (shape action via fields)
                adjusted_action = self.constraint_propagator.adjust_action(proposed_action)

                # Apply ethical pressure
                ethically_adjusted = self.ethics_engine.apply_ethical_pressure(adjusted_action)

                # Final ethical check
                is_ethical, ethical_reasoning = self.ethics_engine.should_permit_action(ethically_adjusted)

                if not is_ethical:
                    logger.warning(f"Ethics engine blocked action: {ethical_reasoning}")
                    continue

                # Execute!
                self._execute_action(
                    symbol=symbol,
                    action=ethically_adjusted,
                    intent_id=intent_id,
                    model_type=best_model
                )

            except Exception as e:
                logger.exception(f"Error resolving intent for {symbol}: {e}")

    def _detect_regime_for_symbol(self, symbol: str) -> MarketRegime:
        """Detect market regime for a symbol."""
        try:
            candles_1h = self.weex.get_candles(symbol=symbol, interval='1H', limit=120)
            candles_4h = self.weex.get_candles(symbol=symbol, interval='4H', limit=120)

            closes_1h = self._extract_closes(candles_1h)
            closes_4h = self._extract_closes(candles_4h)

            if len(closes_1h) < 50 and len(closes_4h) < 50:
                return MarketRegime.UNKNOWN

            regime_1h = self.regime_detector_v2.detect_regime(np.array(closes_1h)) if len(closes_1h) >= 50 else None
            regime_4h = self.regime_detector_v2.detect_regime(np.array(closes_4h)) if len(closes_4h) >= 50 else None

            chosen = regime_1h or regime_4h
            if regime_1h and regime_4h:
                if regime_1h.regime in {RegimeType.HIGH_VOLATILITY, RegimeType.LOW_VOLATILITY}:
                    chosen = regime_1h
                elif regime_4h.regime in {RegimeType.HIGH_VOLATILITY, RegimeType.LOW_VOLATILITY}:
                    chosen = regime_4h
                else:
                    chosen = regime_4h if abs(regime_4h.trend_strength) >= abs(regime_1h.trend_strength) else regime_1h

            if not chosen:
                return MarketRegime.UNKNOWN

            mapped = self._map_regime_type(chosen.regime)
            logger.info(
                "Regime detected: {} (confidence={:.2f}, trend={:.3f}, vol_pct={:.1f})",
                mapped.value,
                chosen.confidence,
                chosen.trend_strength,
                chosen.volatility_percentile
            )
            logger.debug(
                "Regime detected for {}: {} (confidence={:.2f}, trend={:.3f}, vol_pct={:.1f})",
                symbol,
                mapped.value,
                chosen.confidence,
                chosen.trend_strength,
                chosen.volatility_percentile
            )
            return mapped

        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return MarketRegime.UNKNOWN

    def _extract_closes(self, candles: Any) -> List[float]:
        closes = []
        if isinstance(candles, dict) and 'data' in candles:
            data = candles['data']
        elif isinstance(candles, list):
            data = candles
        else:
            return closes

        for c in data:
            if isinstance(c, dict):
                closes.append(float(c.get('close', 0)))
            elif isinstance(c, list) and len(c) >= 5:
                closes.append(float(c[4]))
        return closes

    def _map_regime_type(self, regime: RegimeType) -> MarketRegime:
        mapping = {
            RegimeType.STRONG_BULL: MarketRegime.STRONG_UPTREND,
            RegimeType.WEAK_BULL: MarketRegime.WEAK_UPTREND,
            RegimeType.RANGING: MarketRegime.SIDEWAYS,
            RegimeType.WEAK_BEAR: MarketRegime.WEAK_DOWNTREND,
            RegimeType.STRONG_BEAR: MarketRegime.STRONG_DOWNTREND,
            RegimeType.HIGH_VOLATILITY: MarketRegime.HIGH_VOLATILITY,
            RegimeType.LOW_VOLATILITY: MarketRegime.LOW_VOLATILITY,
        }
        return mapping.get(regime, MarketRegime.UNKNOWN)

    def _regime_profile(self, regime: MarketRegime) -> Dict[str, float]:
        if regime == MarketRegime.STRONG_UPTREND:
            return {'size_pct': 0.035, 'stop_loss_pct': 0.010, 'take_profit_pct': 0.025}
        if regime == MarketRegime.STRONG_DOWNTREND:
            return {'size_pct': 0.050, 'stop_loss_pct': 0.010, 'take_profit_pct': 0.025}
        if regime in {MarketRegime.WEAK_UPTREND, MarketRegime.WEAK_DOWNTREND}:
            return {'size_pct': 0.025, 'stop_loss_pct': 0.008, 'take_profit_pct': 0.020}
        if regime == MarketRegime.SIDEWAYS:
            return {'size_pct': 0.015, 'stop_loss_pct': 0.006, 'take_profit_pct': 0.015}
        if regime == MarketRegime.HIGH_VOLATILITY:
            return {'size_pct': 0.015, 'stop_loss_pct': 0.012, 'take_profit_pct': 0.020}
        if regime == MarketRegime.LOW_VOLATILITY:
            return {'size_pct': 0.020, 'stop_loss_pct': 0.006, 'take_profit_pct': 0.012}
        return {'size_pct': 0.020, 'stop_loss_pct': 0.008, 'take_profit_pct': 0.018}

    def _generate_action(
        self,
        symbol: str,
        model_type: ModelType,
        regime: MarketRegime,
        intent: Intent,
        context: Dict
    ) -> Optional[Dict]:
        """
        Generate a proposed action using bandit-selected strategy.

        PHASE 2 PIPELINE:
        1. Bandit selects strategy for (symbol, regime)
        2. Generate signal using selected strategy
        3. Build trade intent with features
        """
        logger.info("DIAG_ENTRY symbol={} regime={}", symbol, regime)
        # Get current price
        try:
            ticker = self.weex.get_ticker(symbol)
            if 'data' in ticker:
                price = float(ticker['data'].get('last', 0))
            else:
                price = float(ticker.get('last', 0))
        except Exception as e:
            logger.info("DIAG_EARLY symbol={} stage=ticker_error err={}", symbol, e)
            return None

        # Fetch candles for strategy
        try:
            candles = self.weex.get_candles(symbol=symbol, interval='1H', limit=100)
        except Exception as e:
            logger.info("DIAG_EARLY symbol={} stage=candles_error err={}", symbol, e)
            return None

        # PHASE 2: Bandit selects strategy
        regime_str = regime.value if hasattr(regime, 'value') else str(regime)
        chosen_strategy = self.bandit.select_strategy(symbol, regime_str)

        if regime == MarketRegime.LOW_VOLATILITY:
            chosen_strategy = 'momentum'
            logger.info("LOW_VOL OVERRIDE: forcing chosen_strategy=momentum for {}", symbol)

        logger.debug(f"Bandit selected strategy: {chosen_strategy} for {symbol} in {regime_str}")

        # Generate signal using chosen strategy
        if chosen_strategy == 'flat':
            # Bandit learned best action is no action
            logger.info("DIAG_EARLY symbol={} stage=bandit_flat", symbol)
            return {'direction': 'HOLD', 'confidence': 0.0, 'strategy': 'flat'}
        elif chosen_strategy == 'momentum':
            logger.info("DIAG_MOMENTUM_INPUT symbol={} candles={}", symbol, (len(candles) if candles is not None else None))
            logger.info("DIAG_MOMENTUM_ENGINE_CLASS symbol={} strategy_class={} strategy_module={} engine_class={} engine_module={}", symbol, self.momentum_strategy.__class__.__name__, self.momentum_strategy.__class__.__module__, getattr(self.momentum_strategy, 'momentum_engine', self.momentum_strategy).__class__.__name__, getattr(self.momentum_strategy, 'momentum_engine', self.momentum_strategy).__class__.__module__)
            logger.info("DIAG_CALL_MOMENTUM symbol={} regime={}", symbol, regime)
            signal = self.momentum_strategy.generate_signal(candles, price, symbol, regime=regime)
            has_signal = bool(signal)
            logger.info("DIAG_MOMENTUM_RESULT symbol={} has_signal={}", symbol, has_signal)
            self._track_gate_counts(signal, regime)
        else:
            # Fallback to momentum if strategy not implemented yet
            signal = self.momentum_strategy.generate_signal(candles, price, symbol, regime=regime)
            has_signal = bool(signal)
            logger.info("DIAG_MOMENTUM_RESULT symbol={} has_signal={}", symbol, has_signal)
            self._track_gate_counts(signal, regime)
            chosen_strategy = 'momentum'

        if not signal:
            logger.info("DIAG_EARLY symbol={} stage=no_signal", symbol)
            return {'direction': 'HOLD', 'confidence': 0.0}

        if not isinstance(signal, dict):
            logger.info(
                "DIAG_EARLY symbol={} stage=signal_not_dict type={} value={}",
                symbol,
                type(signal).__name__,
                signal
            )
            return {'direction': 'HOLD', 'confidence': 0.0, 'reason': str(signal)}

        # Position sizing + stops based on regime profile
        profile = self._regime_profile(regime)
        if self.iteration == 1:
            logger.info("=== ADAPTIVE TRADING SYSTEM START ===")
            logger.info(
                "Initial regime: {}, Profile: size={:.3f} stop={:.3f} take_profit={:.3f}",
                regime.value if hasattr(regime, "value") else str(regime),
                profile['size_pct'],
                profile['stop_loss_pct'],
                profile['take_profit_pct']
            )
            logger.info("Contest equity: ${:.2f}", self.current_capital)
        logger.info(
            "Applying {} profile: size={:.3f}, stop={:.3f}, take_profit={:.3f}",
            regime.value if hasattr(regime, "value") else str(regime),
            profile['size_pct'],
            profile['stop_loss_pct'],
            profile['take_profit_pct']
        )
        if symbol in self.tier_a_pairs:
            tier_risk_pct = self.tier_a_risk_pct
            tier_label = "A"
        elif symbol in self.tier_b_pairs:
            tier_risk_pct = self.tier_b_risk_pct
            tier_label = "B"
        else:
            tier_risk_pct = self.tier_c_risk_pct
            tier_label = "C"

        signal_reason = signal.get('reason', '')
        if not signal_reason:
            signal_reason = "LEGACY_NONE"
        entry_meta = signal.get('entry_meta')
        if not isinstance(entry_meta, dict):
            entry_meta = {}
        regime_str_l = regime_str.lower() if isinstance(regime_str, str) else str(regime_str).lower()
        symbol_l = symbol.lower()

        position_size_pct = tier_risk_pct
        logger.info("Tier {} sizing: size_pct={:.3f}", tier_label, position_size_pct)

        probe_thresholds = entry_meta.get("thresholds")
        probe_gates = entry_meta.get("gates")
        probe_vol_bucket = entry_meta.get("vol_bucket")
        probe_atr_ratio = entry_meta.get("atr_ratio")

        signal_probe_requested = bool(signal.get("probe_mode"))
        probe_mode = (
            self.probe_mode_enabled
            and signal_reason == self.probe_entry_reason
            and symbol_l in self.probe_override_allowlist
        )
        if signal_probe_requested and not probe_mode:
            logger.info(
                "PROBE_MODE_SIGNAL_IGNORED symbol={} reason={} probe_enabled={} in_allowlist={} expected_reason={}",
                symbol,
                signal_reason,
                self.probe_mode_enabled,
                symbol_l in self.probe_override_allowlist,
                self.probe_entry_reason,
            )

        size_scale = 1.0
        size_scale_pre_stealth = 1.0
        if probe_mode:
            size_scale *= self.probe_size_multiplier
            logger.info(
                "PROBE_MODE=1 symbol={} reason={} size_scale={:.3f} allowlist={}",
                symbol,
                signal_reason,
                size_scale,
                sorted(self.probe_override_allowlist),
            )

        entry_meta.setdefault("entry_reason", signal_reason)
        entry_meta.setdefault("symbol", symbol)
        entry_meta.setdefault("regime", regime_str)
        entry_meta.setdefault("probe_mode", probe_mode)

        champion_level = 1.00
        champion_multiplier = 1.00
        champion_scale_applied = False
        champion_quarantined = False
        champion_quarantine_until_ms = 0
        champion_tuple_key = self._tuple_key(symbol, signal_reason, regime_str)

        if self.champion_ladder_enabled:
            champion_eval = self._evaluate_champion_tuple(
                symbol=symbol,
                entry_reason=signal_reason,
                regime=regime_str,
            )
            champion_level = float(champion_eval.get("level", 1.0) or 1.0)
            champion_multiplier = float(champion_eval.get("multiplier", 1.0) or 1.0)
            champion_quarantined = bool(champion_eval.get("quarantine_active"))
            champion_quarantine_until_ms = int(champion_eval.get("quarantine_until_ms", 0) or 0)
            champion_tuple_key = str(champion_eval.get("tuple_key") or champion_tuple_key)
            if not champion_quarantined and champion_multiplier > 1.0:
                size_scale *= champion_multiplier
                champion_scale_applied = True
                logger.info(
                    "CHAMPION_APPLIED tuple={} level={:.2f} multiplier={:.2f}",
                    champion_tuple_key,
                    champion_level,
                    champion_multiplier,
                )
        else:
            champion_tuple_ready = bool(self.champion_symbol and self.champion_entry_reason and self.champion_regime)
            if self.champion_tuple_enabled:
                if not champion_tuple_ready:
                    if not self._champion_tuple_warned_incomplete:
                        logger.warning(
                            "CHAMPION_SCALE_SKIPPED reason=incomplete_tuple symbol={} entry_reason={} regime={}",
                            self.champion_symbol or "<empty>",
                            self.champion_entry_reason or "<empty>",
                            self.champion_regime or "<empty>",
                        )
                        self._champion_tuple_warned_incomplete = True
                else:
                    champion_symbol_ok = symbol_l == self.champion_symbol
                    champion_reason_ok = signal_reason == self.champion_entry_reason
                    champion_regime_ok = regime_str_l == self.champion_regime
                    if champion_symbol_ok and champion_reason_ok and champion_regime_ok:
                        size_scale *= self.champion_size_multiplier
                        champion_multiplier = self.champion_size_multiplier
                        champion_level = champion_multiplier
                        champion_scale_applied = True
                        logger.info(
                            "CHAMPION_SCALE_APPLIED=1 symbol={} reason={} regime={} multiplier={:.3f}",
                            symbol,
                            signal_reason,
                            regime_str,
                            self.champion_size_multiplier,
                        )

        size_scale_pre_stealth = size_scale
        stealth_profile = self._get_stealth_profile(
            symbol=symbol,
            entry_reason=signal_reason,
            regime=regime_str,
            champion_level=champion_level,
        )
        if self.stealth_mode_enabled:
            size_scale *= float(stealth_profile.get("size_jitter_mult", 1.0) or 1.0)

        unclamped_size_scale = size_scale
        size_scale = max(self.stealth_min_size_scale, min(self.stealth_max_size_scale, size_scale))
        if probe_mode and size_scale > self.probe_size_multiplier:
            size_scale = self.probe_size_multiplier
        if abs(size_scale - unclamped_size_scale) > 1e-9:
            logger.info(
                "SIZE_SCALE_CLAMPED symbol={} tuple={} pre={:.4f} post={:.4f} probe_mode={}",
                symbol,
                champion_tuple_key,
                unclamped_size_scale,
                size_scale,
                probe_mode,
            )
        logger.info(
            "STEALTH_APPLIED symbol={} tuple={} time_jitter_ms={} size_jitter_mult={:.4f} final_size_scale={:.4f}",
            symbol,
            stealth_profile.get("tuple_key"),
            int(stealth_profile.get("time_jitter_ms", 0) or 0),
            float(stealth_profile.get("size_jitter_mult", 1.0) or 1.0),
            size_scale,
        )

        entry_meta["champion_tuple_key"] = champion_tuple_key
        entry_meta["champion_level"] = champion_level
        entry_meta["champion_multiplier"] = champion_multiplier
        entry_meta["champion_quarantined"] = champion_quarantined
        entry_meta["champion_quarantine_until_ms"] = champion_quarantine_until_ms
        entry_meta["stealth_bucket"] = stealth_profile.get("bucket")
        entry_meta["stealth_time_jitter_ms"] = stealth_profile.get("time_jitter_ms")
        entry_meta["stealth_size_jitter_mult"] = stealth_profile.get("size_jitter_mult")
        entry_meta["size_scale_pre_stealth"] = size_scale_pre_stealth
        entry_meta["size_scale_post_stealth"] = size_scale

        balance_value = float(context.get('balance') or 0.0)
        position_value = balance_value * position_size_pct * size_scale
        size = position_value / price

        # Pre-round size to avoid precision issues - defensive measure
        # WEEX requires sizes to match stepSize increments
        import decimal
        step_sizes = {
            'cmt_btcusdt': 0.001, 'cmt_ethusdt': 0.01, 'cmt_solusdt': 0.1,
            'cmt_dogeusdt': 100.0, 'cmt_xrpusdt': 10.0, 'cmt_adausdt': 10.0,
            'cmt_bnbusdt': 0.1, 'cmt_ltcusdt': 0.1  # DOGE=100, XRP/ADA=10 from API
        }
        step = step_sizes.get(symbol, 0.1)
        d_size = decimal.Decimal(str(size))
        d_step = decimal.Decimal(str(step))
        size = float((d_size // d_step) * d_step)

        # Extract features for journal logging
        features = signal.get('features', {})
        momentum_pct = features.get('momentum_pct')
        rsi = features.get('rsi')
        atr = features.get('atr')
        funding_rate = features.get('funding_rate')

        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        stop_loss_pct = signal.get('stop_loss_pct')
        take_profit_pct = signal.get('take_profit_pct')
        if stop_loss is None and not stop_loss_pct:
            stop_loss_pct = profile['stop_loss_pct']
        if stop_loss is None and stop_loss_pct:
            if signal['direction'] == 'LONG':
                stop_loss = price * (1 - stop_loss_pct)
            else:
                stop_loss = price * (1 + stop_loss_pct)
        if take_profit is None and not take_profit_pct:
            take_profit_pct = profile['take_profit_pct']
        if take_profit is None and take_profit_pct:
            if signal['direction'] == 'LONG':
                take_profit = price * (1 + take_profit_pct)
            else:
                take_profit = price * (1 - take_profit_pct)

        positions_snapshot = self.position_ledger.get_all_positions()
        current_positions = len(positions_snapshot)
        _, margin_used_live, total_notional_live = self._calculate_position_metrics(positions_snapshot)
        gross_cap_pct, profit_lock_active = self._effective_gross_exposure_cap()
        gross_exposure_pct = (
            (total_notional_live / self.current_capital)
            if self.current_capital and self.current_capital > 0
            else None
        )
        margin_ratio = (
            (margin_used_live / self.current_capital)
            if self.current_capital and self.current_capital > 0
            else None
        )
        risk_headroom = {
            "gross_exposure_cap_pct": gross_cap_pct,
            "gross_exposure_current_pct": gross_exposure_pct,
            "gross_exposure_remaining_pct": (
                max(0.0, gross_cap_pct - gross_exposure_pct)
                if gross_exposure_pct is not None
                else None
            ),
            "profit_lock_active": profit_lock_active,
            "max_margin_ratio": getattr(self.risk_manager, "max_margin_ratio", None),
            "margin_ratio_current": margin_ratio,
            "margin_ratio_remaining": (
                max(0.0, float(getattr(self.risk_manager, "max_margin_ratio", 0.0)) - margin_ratio)
                if margin_ratio is not None
                else None
            ),
        }

        action = {
            'symbol': symbol,
            'direction': signal['direction'],
            'confidence': signal['confidence'],
            'entry_price': price,
            'position_size': size,
            'max_leverage': 15.0,
            'risk_reward_ratio': 3.0,
            'reason': signal_reason,
            'strategy': chosen_strategy,
            'regime': regime_str,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            # Features for journal
            'features': features,
            'entry_meta': entry_meta,
            'probe_mode': probe_mode,
            'probe_symbol_allowlist': sorted(self.probe_override_allowlist),
            'size_scale': size_scale,
            'size_scale_pre_stealth': size_scale_pre_stealth,
            'stealth_mode_applied': self.stealth_mode_enabled,
            'stealth_bucket': stealth_profile.get("bucket"),
            'stealth_time_jitter_ms': int(stealth_profile.get("time_jitter_ms", 0) or 0),
            'stealth_size_jitter_mult': float(stealth_profile.get("size_jitter_mult", 1.0) or 1.0),
            'champion_scale_applied': champion_scale_applied,
            'champion_tuple_key': champion_tuple_key,
            'champion_level': champion_level,
            'champion_multiplier': champion_multiplier,
            'champion_quarantined': champion_quarantined,
            'champion_quarantine_until_ms': champion_quarantine_until_ms,
            'gates_evaluated': probe_gates,
            'gate_thresholds': probe_thresholds,
            'vol_bucket': probe_vol_bucket,
            'atr_ratio': probe_atr_ratio,
            'risk_headroom': risk_headroom,
            'profit_lock_active': profit_lock_active,
            'size_floor_applied': False,
        }

        strategy_explanation = (
            "Eval: regime={regime}, mom={mom}, rsi={rsi}, atr={atr}; "
            "entry_reason={reason} selected_action={direction} conf={conf} over=HOLD; "
            "probe={probe} scale={scale} champion={champion} level={champion_level}; "
            "gates={gates} thresholds={thresholds} risk_headroom={risk_headroom}."
        ).format(
            regime=regime_str,
            mom=momentum_pct,
            rsi=rsi,
            atr=atr,
            reason=action.get("reason"),
            direction=action.get("direction"),
            conf=action.get("confidence"),
            probe=probe_mode,
            scale=f"{size_scale:.3f}",
            champion=champion_scale_applied,
            champion_level=f"{champion_level:.2f}",
            gates=probe_gates,
            thresholds=probe_thresholds,
            risk_headroom=risk_headroom,
        )
        if len(strategy_explanation) > 1000:
            strategy_explanation = strategy_explanation[:997] + "..."

        self._emit_ai_log(
            stage="Strategy Evaluation",
            model=f"SDM:{chosen_strategy}",
            input_payload={
                "symbol": symbol,
                "regime": regime_str,
                "strategy": chosen_strategy,
                "price": price,
                "balance": context.get("balance"),
                "signal": action.get("reason"),
                "entry_reason": action.get("reason"),
                "momentum_pct": momentum_pct,
                "rsi": rsi,
                "atr": atr,
                "funding_rate": funding_rate,
                "current_positions": current_positions,
                "risk_headroom": risk_headroom,
                "profit_lock_active": profit_lock_active,
                "probe_mode": probe_mode,
                "probe_symbol_allowlist": sorted(self.probe_override_allowlist),
                "size_scale": size_scale,
                "size_scale_pre_stealth": size_scale_pre_stealth,
                "stealth_mode_applied": self.stealth_mode_enabled,
                "stealth_bucket": stealth_profile.get("bucket"),
                "stealth_time_jitter_ms": int(stealth_profile.get("time_jitter_ms", 0) or 0),
                "stealth_size_jitter_mult": float(stealth_profile.get("size_jitter_mult", 1.0) or 1.0),
                "champion_scale_applied": champion_scale_applied,
                "champion_tuple_key": champion_tuple_key,
                "champion_level": champion_level,
                "champion_multiplier": champion_multiplier,
                "champion_quarantined": champion_quarantined,
                "champion_quarantine_until_ms": champion_quarantine_until_ms,
                "gates_evaluated": probe_gates,
                "thresholds": probe_thresholds,
                "vol_bucket": probe_vol_bucket,
                "atr_ratio": probe_atr_ratio,
                "size_floor_applied": action.get("size_floor_applied"),
                "entry_meta": entry_meta,
            },
            output_payload={
                "direction": action.get("direction"),
                "confidence": action.get("confidence"),
                "entry_price": action.get("entry_price"),
                "position_size": action.get("position_size"),
                "stop_loss": action.get("stop_loss"),
                "take_profit": action.get("take_profit"),
                "order_params": {
                    "entry_price": action.get("entry_price"),
                    "position_size": action.get("position_size"),
                    "stop_loss": action.get("stop_loss"),
                    "take_profit": action.get("take_profit"),
                },
                "size_scale": size_scale,
                "probe_mode": probe_mode,
                "champion_scale_applied": champion_scale_applied,
                "champion_level": champion_level,
                "champion_multiplier": champion_multiplier,
                "stealth_time_jitter_ms": int(stealth_profile.get("time_jitter_ms", 0) or 0),
                "stealth_size_jitter_mult": float(stealth_profile.get("size_jitter_mult", 1.0) or 1.0),
            },
            explanation=strategy_explanation
        )

        logger.info(
            "DIAG_ACTION symbol={} regime={} out={}",
            symbol,
            regime_str,
            action
        )

        if entry_meta:
            safe_meta = self._sanitize_meta(entry_meta)
            try:
                meta_json = json.dumps(safe_meta, separators=(",", ":"), ensure_ascii=True)
            except Exception:
                meta_json = str(safe_meta)
            logger.info("DIAG_ENTRY_META symbol={} entry_reason={} payload={}", symbol, safe_meta.get("entry_reason") if isinstance(safe_meta, dict) else None, meta_json)

        return action

    def _execute_action(
        self,
        symbol: str,
        action: Dict,
        intent_id: str,
        model_type: ModelType
    ):
        """
        PHASE 2 EXECUTION PIPELINE - Execute trading action with full guardrails.

        Pipeline order (NON-NEGOTIABLE):
        1. Build TradeIntent
        2. Position Ledger gate
        3. Risk Manager veto
        4. Decision Journal log (ALWAYS, even if blocked)
        5. Execute order (if gates pass and not DRY_RUN)
        6. Update ledger + journal after execution
        """
        try:
            logger.info(f"\n{'*'*60}")
            logger.info(f"PHASE 2 EXECUTION PIPELINE - {symbol}")
            logger.info(f"Strategy: {action.get('strategy', 'unknown')}")
            logger.info(f"Direction: {action['direction']}")
            logger.info(f"Size: {action.get('position_size', 0):.6f}")
            logger.info(f"Price: ${action.get('entry_price', 0):.2f}")
            logger.info(f"Confidence: {action.get('confidence', 0.0):.2f}")
            logger.info(f"{'*'*60}")

            # Skip HOLD signals
            if action['direction'] == 'HOLD':
                return

            if action.get('reason') == 'LOW_VOL_EXTREME_OVERRIDE':
                self._diag_block_counts["override_signals"] += 1

            if self.diagnostic_suspend_active:
                self._log_diagnostic_status()
                logger.warning("🟠 DIAGNOSTIC_SUSPEND - blocking order execution for {}", symbol)
                return

            self._evaluate_bnb_tactical_quarantine()
            if self._is_bnb_tactically_quarantined(symbol):
                logger.warning(
                    "BNB_TACTICAL_QUARANTINE_BLOCKED symbol={} until={} stage=execute_action",
                    symbol,
                    int(self._get_bnb_tactical_quarantine_until()),
                )
                return

            if self._is_symbol_quarantined(symbol):
                quarantine_until = self._get_symbol_quarantine_until(symbol)
                logger.warning(
                    "SYMBOL_QUARANTINED_BLOCK symbol={} until={} stage=execute_action",
                    symbol,
                    int(float(quarantine_until or 0.0)),
                )
                return

            self._log_straddle_signal_debug(
                symbol=symbol,
                action=action,
                intent_graph_blocked=False
            )

            if self.straddle_manager.is_blocked(symbol):
                logger.info(f"⏸ STRADDLE ACTIVE - skipping execution for {symbol}")
                self._diag_block_counts["blocked_straddle_active"] += 1
                return

            if action.get('reason') == 'LOW_VOL_SHORT_GATE_X3_WITH_ATR':
                logger.info("STRADDLE_BYPASS_LOW_VOL_ATR symbol={} confidence={:.3f}", symbol, float(action.get('confidence', 0.0)))
            else:
                if action.get('confidence', 0.0) >= self.straddle_confidence_threshold:
                    size_scale = float(action.get("size_scale", 1.0) or 1.0)
                    if size_scale <= 0:
                        size_scale = 1.0
                    legacy_for_straddle = self.legacy_amount * size_scale
                    opened = self.straddle_manager.try_open(
                        symbol=symbol,
                        price=action.get('entry_price', 0.0),
                        legacy_amount=legacy_for_straddle,
                        reason=action.get('reason'),
                        entry_meta=action.get('entry_meta'),
                        entry_side=action.get('direction'),
                    )
                    if opened:
                        self._diag_block_counts["opened_straddles"] += 1
                        return
                    logger.warning(f"⚠ STRADDLE NOT OPENED - skipping normal execution for {symbol}")
                    return

            # Map direction to WEEX side
            if action['direction'] == 'LONG':
                side = 1
            elif action['direction'] == 'SHORT':
                side = 2
            else:
                return


            
            
            size_floor_applied = False

            # SIZE_FLOOR_APPLIED: minimum notional floor for LOW_VOL_SHORT_GATE_X3_WITH_ATR shorts
            if action.get('direction') == 'SHORT' and action.get('reason') == 'LOW_VOL_SHORT_GATE_X3_WITH_ATR':
                if action.get('position_size', 0.0) <= 0.0:
                    MIN_NOTIONAL_USDT = 10.0
                    price = action.get('entry_price', 0.0) or 0.0
                    if price > 0:
                        min_qty = MIN_NOTIONAL_USDT / price
                        old_qty = action.get('position_size', 0.0)
                        import decimal
                        step_sizes = {
                            'cmt_btcusdt': 0.001, 'cmt_ethusdt': 0.01, 'cmt_solusdt': 0.1,
                            'cmt_dogeusdt': 100.0, 'cmt_xrpusdt': 10.0, 'cmt_adausdt': 10.0,
                            'cmt_bnbusdt': 0.1, 'cmt_ltcusdt': 0.1
                        }
                        step = step_sizes.get(symbol, 0.1)
                        d_qty = decimal.Decimal(str(min_qty))
                        d_step = decimal.Decimal(str(step))
                        rounded = (d_qty / d_step).to_integral_value(rounding=decimal.ROUND_UP) * d_step
                        action['position_size'] = float(rounded)
                        size_floor_applied = True
                        action["size_floor_applied"] = True
                        logger.info(
                            "SIZE_FLOOR_APPLIED symbol={} reason={} price={:.6f} old_qty={:.8f} new_qty={:.8f} min_notional={:.2f}",
                            symbol, action.get('reason'), price, old_qty, action['position_size'], MIN_NOTIONAL_USDT
                        )
            action.setdefault("size_floor_applied", size_floor_applied)

# Skip if position size too small
            if action['position_size'] <= 0:
                logger.warning(f"Position size too small after rounding, skipping")
                return

            # === STEP 1: Build TradeIntent ===
            trade_intent = TradeIntent(
                symbol=symbol,
                side=action['direction'],
                size=action['position_size'],
                entry_price=action['entry_price'],
                stop_loss=action.get('stop_loss'),
                take_profit=action.get('take_profit'),
                confidence=action.get('confidence', 0.5)
            )

            # === STEP 2: Position Ledger Gate ===
            ledger_approved, ledger_reason = self._can_open_position(symbol, action['direction'])
            if ledger_approved:
                ledger_approved, ledger_reason = self.position_ledger.can_open_position(
                    symbol=symbol,
                    side=action['direction']
                )

            if not ledger_approved:
                logger.warning(f"🚫 LEDGER BLOCKED: {ledger_reason}")

            # === STEP 2.5: HARD CAP - 30% Gross Exposure Limit ===
            # This is a NON-NEGOTIABLE safety limit applied BEFORE risk manager
            gross_exposure_blocked = False
            gross_exposure_reason = ""

            if ledger_approved:
                # Calculate gross notional exposure (recompute to avoid stale cache)
                _, _, total_notional = self._calculate_position_metrics(
                    self.position_ledger.get_all_positions()
                )
                trade_notional = action['position_size'] * action['entry_price']
                new_gross_notional = total_notional + trade_notional
                gross_exposure_pct = new_gross_notional / self.current_capital if self.current_capital > 0 else 0.0

                # Gross exposure cap (optionally tightened in profit-lock mode)
                max_gross_exposure_pct, profit_lock_active = self._effective_gross_exposure_cap()

                if gross_exposure_pct > max_gross_exposure_pct:
                    gross_exposure_blocked = True
                    cap_mode = "profit_lock" if profit_lock_active else "base"
                    gross_exposure_reason = (
                        f"GROSS EXPOSURE CAP EXCEEDED [{cap_mode}]: {gross_exposure_pct:.1%} > {max_gross_exposure_pct:.1%} "
                        f"(current: ${total_notional:.2f}, new trade: ${trade_notional:.2f}, "
                        f"total: ${new_gross_notional:.2f}, balance: ${self.current_capital:.2f})"
                    )
                    logger.error(f"❌ {gross_exposure_reason}")

            # === STEP 3: Risk Manager Veto ===
            risk_approved = True
            veto_reasons = []

            positions = self.position_ledger.get_all_positions()
            unrealized_pnl, margin_used, total_notional = self._calculate_position_metrics(
                positions
            )
            account_state = AccountState(
                balance=self.current_capital,
                equity=self.current_capital,
                margin_used=margin_used,
                unrealized_pnl=unrealized_pnl,
                daily_pnl=self.daily_pnl,
                peak_balance_today=self.peak_balance_today,
                total_notional=total_notional
            )

            if ledger_approved and not gross_exposure_blocked:  # Only check risk if ledger passed AND under gross cap
                # Rebuild symbol exposure from live positions to avoid stale risk veto
                self.risk_manager.symbol_exposure = {}
                for pos in positions:
                    if isinstance(pos, str):
                        continue

                    if isinstance(pos, dict):
                        getter = pos.get
                    else:
                        getter = lambda k, default=None: getattr(pos, k, default)

                    try:
                        size = float(getter('size', 0) or 0)
                    except (TypeError, ValueError):
                        size = 0.0
                    if size == 0.0:
                        continue
                    try:
                        notional = float(getter('open_value', 0) or 0)
                    except (TypeError, ValueError):
                        notional = 0.0
                    if notional == 0.0:
                        mark_price = float(getter('mark_price', 0) or 0)
                        if mark_price > 0:
                            notional = abs(size) * mark_price
                    if notional:
                        self.risk_manager.update_symbol_exposure(getter('symbol'), notional)

                risk_approved, veto_reasons = self.risk_manager.approve(
                    trade_intent,
                    account_state,
                    self.position_ledger.get_all_positions()
                )

                if not risk_approved:
                    logger.error(f"❌ RISK VETO: {[v.message for v in veto_reasons]}")

            block_reason = None
            if not ledger_approved:
                block_reason = ledger_reason
            elif gross_exposure_blocked:
                block_reason = gross_exposure_reason
            elif not risk_approved and veto_reasons:
                block_reason = veto_reasons[0].message

            gate_results = {
                "ledger_ok": ledger_approved,
                "gross_exposure_ok": not gross_exposure_blocked,
                "risk_ok": risk_approved,
                "size_floor_applied": action.get("size_floor_applied"),
                "min_size_floor_applied": action.get("size_floor_applied"),
                "straddle_bypassed": action.get("straddle_bypassed"),
                "probe_mode": action.get("probe_mode"),
                "size_scale": action.get("size_scale"),
                "champion_scale_applied": action.get("champion_scale_applied"),
                "champion_tuple_key": action.get("champion_tuple_key"),
                "champion_level": action.get("champion_level"),
                "champion_quarantined": action.get("champion_quarantined"),
                "champion_quarantine_until_ms": action.get("champion_quarantine_until_ms"),
                "stealth_mode_applied": action.get("stealth_mode_applied"),
                "stealth_time_jitter_ms": action.get("stealth_time_jitter_ms"),
                "stealth_size_jitter_mult": action.get("stealth_size_jitter_mult"),
                "gates_evaluated": action.get("gates_evaluated"),
                "thresholds": action.get("gate_thresholds"),
                "vol_bucket": action.get("vol_bucket"),
                "atr_ratio": action.get("atr_ratio"),
                "risk_headroom": action.get("risk_headroom"),
                "block_reason": block_reason,
            }

            self._emit_ai_log(
                stage="Risk & Constraints",
                model="RiskManagerVeto",
                input_payload={
                    "symbol": symbol,
                    "side": trade_intent.side,
                    "size": trade_intent.size,
                    "entry_price": trade_intent.entry_price,
                    "balance": account_state.balance,
                    "equity": account_state.equity,
                    "margin_used": account_state.margin_used,
                    "gate_results": gate_results,
                },
                output_payload={
                    "approved": risk_approved,
                    "veto_reasons": [v.message for v in veto_reasons],
                    "gate_results": gate_results,
                },
                explanation=(
                    "Risk: ledger_ok={ledger_ok} risk_ok={risk_ok} gross_ok={gross_ok}; "
                    "block_reason={block_reason}."
                ).format(
                    ledger_ok=ledger_approved,
                    risk_ok=risk_approved,
                    gross_ok=not gross_exposure_blocked,
                    block_reason=block_reason,
                )
            )

            # === STEP 4: Decision Journal - ALWAYS LOG ===
            import json
            features = action.get('features', {})

            decision = DecisionTick(
                timestamp=time.time(),
                symbol=symbol,
                regime=action.get('regime', 'unknown'),
                price=action['entry_price'],
                # Features
                rsi=features.get('rsi', 0.0),
                ema_fast=features.get('ema_fast', 0.0),
                ema_slow=features.get('ema_slow', 0.0),
                volume=features.get('volume', 0.0),
                volatility=features.get('volatility', 0.0),
                # Signal
                strategy_name=action.get('strategy', 'unknown'),
                signal_direction=action['direction'],
                signal_confidence=action.get('confidence', 0.0),
                # Proposed action
                proposed_side=action['direction'],
                proposed_size=action['position_size'],
                proposed_entry=action['entry_price'],
                proposed_stop=action.get('stop_loss'),
                proposed_take_profit=action.get('take_profit'),
                # Gates
                ledger_approved=ledger_approved,
                ledger_reason=ledger_reason,
                risk_approved=risk_approved,
                risk_veto_reasons=json.dumps([{
                    'rule': v.rule,
                    'severity': v.severity,
                    'message': v.message,
                    'value': v.value,
                    'limit': v.limit
                } for v in veto_reasons]),
                # Execution (to be updated)
                executed=False,
                execution_reason='pending'
            )

            # Determine if we can execute
            can_execute = ledger_approved and not gross_exposure_blocked and risk_approved

            features = action.get("features", {})
            momentum_pct = features.get("momentum_pct")
            atr = features.get("atr")
            rsi = features.get("rsi")
            confidence = action.get("confidence")
            confidence_str = f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "n/a"

            gate_results = {
                "ledger_ok": ledger_approved,
                "gross_exposure_ok": not gross_exposure_blocked,
                "risk_ok": risk_approved,
                "size_floor_applied": action.get("size_floor_applied"),
                "min_size_floor_applied": action.get("size_floor_applied"),
                "straddle_bypassed": action.get("straddle_bypassed"),
                "probe_mode": action.get("probe_mode"),
                "size_scale": action.get("size_scale"),
                "champion_scale_applied": action.get("champion_scale_applied"),
                "gates_evaluated": action.get("gates_evaluated"),
                "thresholds": action.get("gate_thresholds"),
                "vol_bucket": action.get("vol_bucket"),
                "atr_ratio": action.get("atr_ratio"),
                "risk_headroom": action.get("risk_headroom"),
                "block_reason": block_reason,
            }
            order_params = {
                "entry_price": action.get("entry_price"),
                "position_size": action.get("position_size"),
                "stop_loss": action.get("stop_loss"),
                "take_profit": action.get("take_profit"),
                "leverage_cap": action.get("max_leverage"),
            }
            selected_over = "HOLD" if action.get("direction") != "HOLD" else "NO_TRADE"
            decision_rationale = (
                "Decision: selected={direction} entry_reason={entry_reason} conf={conf} "
                "over={selected_over}; order={order_params}; "
                "gates ledger_ok={ledger_ok} gross_ok={gross_ok} risk_ok={risk_ok}; "
                "probe={probe} size_scale={size_scale} champion={champion}."
            ).format(
                direction=action.get("direction"),
                entry_reason=action.get("reason"),
                conf=confidence_str,
                selected_over=selected_over,
                order_params=order_params,
                ledger_ok=ledger_approved,
                gross_ok=not gross_exposure_blocked,
                risk_ok=risk_approved,
                probe=action.get("probe_mode"),
                size_scale=action.get("size_scale"),
                champion=action.get("champion_scale_applied"),
            )
            if len(decision_rationale) > 1000:
                decision_rationale = decision_rationale[:997] + "..."
            self._emit_ai_log(
                stage="Decision Making",
                model="AlphaGenesis-SDM-v1",
                input_payload={
                    "symbol": symbol,
                    "regime": action.get("regime"),
                    "signal": action.get("reason"),
                    "confidence": confidence,
                    "momentum_pct": momentum_pct,
                    "atr": atr,
                    "rsi": rsi,
                    "probe_mode": action.get("probe_mode"),
                    "probe_symbol_allowlist": action.get("probe_symbol_allowlist"),
                    "size_scale": action.get("size_scale"),
                    "entry_reason": action.get("reason"),
                    "gates_evaluated": action.get("gates_evaluated"),
                    "thresholds": action.get("gate_thresholds"),
                    "vol_bucket": action.get("vol_bucket"),
                    "atr_ratio": action.get("atr_ratio"),
                    "risk_headroom": action.get("risk_headroom"),
                    "size_floor_applied": action.get("size_floor_applied"),
                    "gate_results": gate_results,
                },
                output_payload={
                    "action": action.get("direction"),
                    "position_size": action.get("position_size"),
                    "risk_approved": risk_approved,
                    "ledger_approved": ledger_approved,
                    "gross_exposure_blocked": gross_exposure_blocked,
                    "probe_mode": action.get("probe_mode"),
                    "size_scale": action.get("size_scale"),
                    "champion_scale_applied": action.get("champion_scale_applied"),
                    "champion_tuple_key": action.get("champion_tuple_key"),
                    "champion_level": action.get("champion_level"),
                    "champion_quarantined": action.get("champion_quarantined"),
                    "champion_quarantine_until_ms": action.get("champion_quarantine_until_ms"),
                    "stealth_mode_applied": action.get("stealth_mode_applied"),
                    "stealth_time_jitter_ms": action.get("stealth_time_jitter_ms"),
                    "stealth_size_jitter_mult": action.get("stealth_size_jitter_mult"),
                    "selected_over": selected_over,
                    "order_params": order_params,
                    "gate_results": gate_results,
                },
                explanation=decision_rationale,
            )

            logger.info(
                "AI_DECISION_TRACE symbol={} entry_reason={} probe={} gates=ledger:{} gross_exposure_blocked:{} risk:{} thresholds={} risk_headroom={} action={} order={}",
                symbol,
                action.get("reason"),
                action.get("probe_mode"),
                ledger_approved,
                gross_exposure_blocked,
                risk_approved,
                action.get("gate_thresholds"),
                action.get("risk_headroom"),
                action.get("direction"),
                order_params,
            )

            # === STEP 5: Execute Order (if gates pass) ===
            success = False
            order_id = None
            client_order_id = None

            if not can_execute:
                # Blocked by gates
                if not ledger_approved:
                    decision.executed = False
                    decision.execution_reason = f'ledger_blocked: {ledger_reason}'
                elif gross_exposure_blocked:
                    decision.executed = False
                    decision.execution_reason = f'gross_exposure_cap: {gross_exposure_reason}'
                elif not risk_approved:
                    decision.executed = False
                    decision.execution_reason = f'risk_veto: {veto_reasons[0].rule if veto_reasons else "unknown"}'

                self.journal.log_decision(decision)
                return

            stealth_delay_ms = int(action.get("stealth_time_jitter_ms", 0) or 0)
            if self.stealth_mode_enabled and stealth_delay_ms > 0:
                bounded_delay_ms = min(stealth_delay_ms, self.stealth_time_jitter_ms_max)
                if bounded_delay_ms > 0:
                    time.sleep(float(bounded_delay_ms) / 1000.0)

            # Gates passed - execute or simulate
            if self.dry_run_mode:
                # DRY RUN: Simulate order
                logger.info(f"🟡 DRY_RUN: Would place {action['direction']} order for {symbol}")

                result = {
                    'dry_run': True,
                    'request': {
                        'symbol': symbol,
                        'side': side,
                        'size': action['position_size']
                    }
                }
                success = True  # Treat simulated orders as success
                order_id = f"dry_run_{symbol}_{int(time.time())}"
                client_order_id = order_id

                decision.executed = False  # Not a real execution
                decision.execution_reason = 'dry_run_simulated'
                decision.order_id = order_id

            else:
                # LIVE: Place real order
                result = self.weex.place_order(
                    symbol=symbol,
                    side=side,
                    size=action['position_size'],
                    is_market=True
                )
                if isinstance(result, dict):
                    if self._register_40015_error(
                        symbol=symbol,
                        error_code=result.get("code"),
                        error_msg=result.get("msg") or result.get("error"),
                        source="entry_order",
                    ):
                        logger.warning(
                            "SYMBOL_40015_ERROR symbol={} code={} msg={}",
                            symbol,
                            result.get("code"),
                            str(result.get("msg") or result.get("error") or "")[:220],
                        )

                success = 'order_id' in result or 'client_oid' in result

                # DRY_RUN success override (from bug fix)
                if isinstance(result, dict) and result.get('dry_run'):
                    logger.info(f"🟡 DRY_RUN simulated order accepted: {result.get('request', {})}")
                    success = True

                result_order_id = None
                if isinstance(result, dict):
                    result_order_id = result.get('order_id') or result.get('client_oid')

                exchange_response = {
                    "orderId": result_order_id,
                    "status": result.get("status") if isinstance(result, dict) else None,
                    "msg": result.get("msg") if isinstance(result, dict) else None,
                }
                order_params = {
                    "symbol": symbol,
                    "side": side,
                    "size": action.get("position_size"),
                    "entry_price": action.get("entry_price"),
                    "is_market": True,
                }
                self._emit_ai_log(
                    stage="Order Execution",
                    model=f"SDM:{action.get('strategy', 'unknown')}",
                    input_payload={
                        "symbol": symbol,
                        "side": side,
                        "size": action.get("position_size"),
                        "entry_price": action.get("entry_price"),
                        "order_params": order_params,
                    },
                    output_payload={
                        "success": success,
                        "order_id": result_order_id,
                        "code": result.get("code") if isinstance(result, dict) else None,
                        "msg": result.get("msg") if isinstance(result, dict) else None,
                        "status_code": result.get("status_code") if isinstance(result, dict) else None,
                        "exchange_response": exchange_response,
                    },
                    explanation=(
                        "Exec: size={size} price={price}; orderId={order_id} status={status}."
                    ).format(
                        size=action.get("position_size"),
                        price=action.get("entry_price"),
                        order_id=result_order_id,
                        status=exchange_response.get("status"),
                    ),
                    order_id=result_order_id
                )

                if success:
                    order_id = result.get('order_id') or result.get('client_oid')
                    client_order_id = result.get('client_oid')
                    symbol_norm = self._normalize_symbol(symbol)
                    if symbol_norm:
                        self.error_count_40015.pop(symbol_norm, None)

                    decision.executed = True
                    decision.execution_reason = 'order_placed'
                    decision.order_id = order_id
                else:
                    # Order failed
                    decision.executed = False
                    decision.execution_reason = f"order_failed: {str(result)[:200]}"

                    if 'margin' in str(result).lower():
                        logger.warning(f"⚠ Insufficient margin for {symbol}")

            # Log decision to journal
            self.journal.log_decision(decision)

            # === STEP 6: Update Ledger + Legacy Systems ===
            if success:
                entry_reason = None
                if isinstance(action, dict):
                    entry_meta = action.get("entry_meta")
                    if isinstance(entry_meta, dict):
                        entry_reason = entry_meta.get("entry_reason")
                    if not entry_reason:
                        entry_reason = action.get("reason")
                if not entry_reason:
                    logger.warning(
                        "ATTRIBUTION_WARNING symbol={} stage=OrderExecution issue=missing_entry_reason fallback=unknown",
                        symbol,
                    )
                    entry_reason = "unknown"
                else:
                    entry_reason = str(entry_reason).strip() or "unknown"
                entry_regime = None
                if isinstance(action, dict):
                    entry_meta = action.get("entry_meta")
                    if isinstance(entry_meta, dict):
                        entry_regime = entry_meta.get("regime")
                    if not entry_regime:
                        entry_regime = action.get("regime")
                if not entry_regime:
                    entry_regime = "unknown"
                else:
                    entry_regime = str(entry_regime).strip().lower() or "unknown"

                # Record in position ledger
                position_recorded = self.position_ledger.open_position(
                    symbol=symbol,
                    side=action['direction'],
                    size=action['position_size'],
                    entry_price=action['entry_price'],
                    client_order_id=client_order_id,
                    order_id=order_id,
                    entry_reason=entry_reason,
                    entry_regime=entry_regime,
                )

                if not position_recorded:
                    logger.error(f"⚠️ Order placed but ledger failed to record!")
                else:
                    logger.info(f"✓ Position recorded in ledger")

                # Legacy learning feedback
                feedback = PerformanceFeedback(
                    action_id=f"action_{self.iteration}_{symbol}",
                    intent_id=intent_id,
                    model_type=model_type.value,
                    timestamp=datetime.now(),
                    success=success,
                    pnl=0.0,
                    fitness_score=action.get('confidence', 0.5),
                    context=action
                )
                self.learning_engine.record_feedback(feedback)

                # Intent graph feedback
                fitness_scores = self.intent_graph.evaluate_proposed_action(action)
                self.intent_graph.record_action_result(action, success, fitness_scores)

                # Update counters
                self.daily_trades += 1
                self.last_trade_time = datetime.now()

                logger.info(f"✓ Order executed successfully")

        except Exception as e:
            logger.error(f"Error in execution pipeline: {e}", exc_info=True)

    def _log_straddle_signal_debug(self, symbol: str, action: Dict, intent_graph_blocked: bool):
        """Log detailed signal info for straddle debugging."""
        confidence = action.get('confidence', 0.0)
        direction = action.get('direction', 'UNKNOWN')
        active_straddles = len(self.straddle_manager.active_symbols())
        threshold = self.straddle_confidence_threshold
        logger.info(
            "📡 SIGNAL DEBUG: {} | Action: {} | Confidence: {:.2f} | Threshold: {:.2f} | Active Straddles: {} | "
            "Blocked by Intent Graph: {}",
            symbol,
            direction,
            confidence,
            threshold,
            active_straddles,
            intent_graph_blocked
        )

        price = action.get('entry_price', 0.0)
        if price > 0:
            atr_ratio = self.straddle_manager.get_atr_ratio(symbol, price)
            logger.info(
                "📈 VOLATILITY: {} ATR ratio: {:.2f} | Normal volatility: {}",
                symbol,
                atr_ratio,
                atr_ratio > 0.7
            )

    def _reconcile_position_ledger(self) -> bool:
        """
        Reconcile position ledger with exchange state.

        Returns:
            True if ledger matches exchange, False if mismatch detected
        """
        try:
            # Fetch current positions from exchange
            positions = self._fetch_positions()

            if not positions:
                logger.info("No positions on exchange to reconcile")
                return True

            active_straddles = set()
            if hasattr(self, 'straddle_manager'):
                active_straddles = self.straddle_manager.active_symbols()

            # Convert WEEX positions to ledger format
            exchange_positions = []
            for pos in positions:
                if pos.get('symbol') in active_straddles:
                    continue
                size = float(pos.get('size', 0))
                if size > 0:  # Only active positions
                    exchange_positions.append({
                        'symbol': pos.get('symbol'),
                        'side': pos.get('side', 'LONG'),
                        'size': size
                    })

            # Reconcile with ledger (bidirectional with grace period)
            is_consistent, warnings = self.position_ledger.reconcile_with_exchange(exchange_positions)

            if warnings:
                for warning in warnings:
                    logger.warning(f"  ⚠️ {warning}")

            if not is_consistent:
                logger.critical("❌ LEDGER MISMATCH - ENTERING SAFE MODE")
                logger.critical("   System will HALT new trades until manual reconciliation")
                self.is_running = False  # Stop trading
                return False

            return True

        except Exception as e:
            logger.error(f"Error during ledger reconciliation: {e}", exc_info=True)
            return False

    def _close_all_positions(self):
        """Close all open positions."""
        logger.info("Closing all positions...")
        if self.diagnostic_suspend_active:
            self._log_diagnostic_status()
            logger.warning("🟠 DIAGNOSTIC_SUSPEND - close_all_positions blocked")
            return
        try:
            account = self.weex.get_account()
            if self._handle_weex_response(account, "account"):
                return
            positions = account.get('position', [])
            if not positions:
                logger.info("No open positions to close")
                return

            for pos in positions:
                size = float(pos.get('size', 0))
                if size <= 0:
                    continue

                symbol = pos.get('symbol')
                side_value = pos.get('side', 1)
                if isinstance(side_value, str):
                    side_str = side_value.upper()
                else:
                    side_str = 'LONG' if int(side_value) == 1 else 'SHORT'

                close_side = 3 if side_str == 'LONG' else 4

                if self.dry_run_mode:
                    logger.info(f"🟡 DRY_RUN: Would close {side_str} {symbol} size={size}")
                    continue

                result = self.weex.place_order(
                    symbol=symbol,
                    side=close_side,
                    size=size,
                    is_market=True
                )
                logger.info(f"Close order result for {symbol}: {result}")
        except Exception as e:
            logger.error(f"Failed closing positions: {e}", exc_info=True)

    def _update_symbol_selection(self, balance: float):
        """After 72h, conditionally add ETH if BTC performed >12%."""
        if self.btc_base_balance is None:
            self.btc_base_balance = balance

        elapsed = time.time() - self.start_time
        if elapsed < self.btc_only_period:
            self.active_symbols = ["cmt_btcusdt"]
            return

        if self.btc_base_balance <= 0:
            return

        btc_performance = (balance - self.btc_base_balance) / self.btc_base_balance
        if btc_performance > 0.12 and "cmt_ethusdt" not in self.active_symbols:
            self.active_symbols.append("cmt_ethusdt")
            logger.info(f"✅ BTC performance {btc_performance*100:.1f}% > 12% - ADDING ETH")
            logger.info(f"🔀 Active symbols: {self.active_symbols}")

    def _update_gamma_mode(self):
        """Detect gamma squeeze and toggle high-volatility parameters."""
        symbol = self.active_symbols[0] if self.active_symbols else "cmt_btcusdt"
        gamma = self._detect_gamma_squeeze(symbol)
        if gamma != self.gamma_squeeze_active:
            self.gamma_squeeze_active = gamma
            if hasattr(self, "straddle_manager"):
                self.straddle_manager.set_gamma_mode(gamma)

    def _detect_gamma_squeeze(self, symbol: str) -> bool:
        """
        Proxy gamma squeeze detection using price acceleration + volume spike.
        Funding rate is not available in the current WEEX client.
        """
        try:
            candles = self.weex.get_candles(symbol=symbol, interval="1m", limit=60)
            if isinstance(candles, dict) and "data" in candles:
                data = candles["data"]
            else:
                data = candles

            if not isinstance(data, list) or len(data) < 10:
                return False

            closes = []
            volumes = []
            for c in data:
                if isinstance(c, dict):
                    closes.append(float(c.get("close", 0)))
                    volumes.append(float(c.get("volume", 0)))
                elif isinstance(c, list) and len(c) >= 6:
                    closes.append(float(c[4]))
                    volumes.append(float(c[5]))

            if len(closes) < 6 or len(volumes) < 6:
                return False

            ref = closes[-6]
            if ref <= 0:
                return False
            recent_return = (closes[-1] - ref) / ref
            price_acceleration = abs(recent_return) > 0.02

            recent_volume = sum(volumes[-5:])
            prior_volume = sum(volumes[:-5])
            if prior_volume <= 0:
                return False
            avg_prior = prior_volume / max(1, (len(volumes) - 5))
            volume_ratio = recent_volume / (avg_prior * 5) if avg_prior > 0 else 0.0
            volume_spike = volume_ratio > 10

            gamma_squeeze = price_acceleration and volume_spike
            if gamma_squeeze:
                logger.warning(
                    "⚠️ GAMMA SQUEEZE DETECTED: {} | Accel: {:.2f}% | Volume: {:.1f}x",
                    symbol,
                    recent_return * 100,
                    volume_ratio
                )
            return gamma_squeeze
        except Exception as e:
            logger.warning(f"Gamma squeeze detection failed for {symbol}: {e}")
            return False

    def _effective_gross_exposure_cap(self) -> tuple[float, bool]:
        """
        Return active gross exposure cap and whether profit-lock mode is engaged.
        Profit lock tightens new-entry exposure once daily PnL reaches a threshold.
        """
        cap = self.max_gross_exposure_pct
        profit_lock_active = False
        if self.profit_lock_enabled and self.daily_pnl_percent >= self.profit_lock_trigger_pnl_pct:
            cap = min(cap, self.profit_lock_gross_exposure_pct)
            profit_lock_active = True

        if self._profit_lock_last_active is None or self._profit_lock_last_active != profit_lock_active:
            logger.info(
                "PROFIT_LOCK_STATUS active={} daily_pnl_pct={:.4f} trigger_pct={:.4f} gross_cap_pct={:.3f}",
                profit_lock_active,
                float(self.daily_pnl_percent),
                float(self.profit_lock_trigger_pnl_pct),
                float(cap),
            )
            self._profit_lock_last_active = profit_lock_active

        return cap, profit_lock_active

    def _log_sdm_status(self):
        """Log SDM system status."""
        pnl = self.current_capital - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        gross_cap_pct, profit_lock_active = self._effective_gross_exposure_cap()
        cap_mode = "profit_lock" if profit_lock_active else "base"

        logger.info(f"\n{'='*70}")
        logger.info("SDM SYSTEM STATUS")
        logger.info(f"{'='*70}")
        logger.info(f"Capital: ${self.current_capital:,.2f} (P&L: ${pnl:+,.2f} / {pnl_pct:+.2f}%)")
        logger.info(f"Daily Trades: {self.daily_trades}")
        logger.info(
            "Risk Cap: gross_exposure={:.1f}% mode={} daily_pnl={:+.2f}% trigger={:.2f}%",
            gross_cap_pct * 100.0,
            cap_mode,
            self.daily_pnl_percent * 100.0,
            self.profit_lock_trigger_pnl_pct * 100.0,
        )

        # Intent graph status
        ig_status = self.intent_graph.get_state_summary()
        logger.info(f"\nIntent Graph: Step {ig_status['time_step']}, "
                   f"{ig_status['active_nodes']}/{ig_status['total_nodes']} active")
        for intent in ig_status['most_active'][:2]:
            logger.info(f"  - {intent['goal'][:50]}: activation={intent['activation']:.2f}")

        # Learning status
        learning_metrics = self.learning_engine.get_learning_metrics()
        if 'error' not in learning_metrics:
            logger.info(f"\nLearning: {learning_metrics['total_feedback']} feedbacks, "
                       f"success rate={learning_metrics['recent_success_rate']:.1%}")

        # Constraint violations
        violations = self.constraint_propagator.get_constraint_violations()
        if violations:
            logger.warning(f"\nConstraint Violations: {len(violations)}")
            for v in violations[:3]:
                logger.warning(f"  - {v['field']}: {v.get('severity', 'UNKNOWN')}")

        # Ethics summary
        ethics_summary = self.ethics_engine.get_violation_summary()
        logger.info(f"\nEthics: {ethics_summary.get('total_violations', 0)} violations total, "
                   f"rate={ethics_summary.get('violation_rate', 0):.1%}")

        logger.info(f"{'='*70}\n")

    def _maybe_run_feedback_loop(self):
        now = time.time()
        if (now - self.last_feedback_ts) < self.feedback_interval_seconds:
            return

        self.last_feedback_ts = now
        cutoff = now - self.feedback_interval_seconds
        recent_trades = self.journal.get_recent_trades(limit=200)
        recent = [t for t in recent_trades if t.get('timestamp', 0) >= cutoff]
        if not recent:
            logger.info("Feedback loop: no trades in last 4h, no adjustments")
            return

        realized = [t.get('realized_pnl', 0.0) or 0.0 for t in recent]
        wins = sum(1 for pnl in realized if pnl > 0)
        avg_pnl = sum(realized) / max(1, len(realized))
        win_rate = wins / max(1, len(realized))

        if avg_pnl < 0 or win_rate < 0.4:
            old_exploration = self.bandit.exploration_rate
            old_straddle = self.straddle_confidence_threshold
            self.bandit.exploration_rate = max(0.05, self.bandit.exploration_rate - 0.05)
            self.straddle_confidence_threshold = min(0.65, self.straddle_confidence_threshold + 0.05)
            logger.warning(
                "Feedback loop: weak performance (avg_pnl={:.2f}, win_rate={:.1f}%). "
                "Exploration={:.2f}, straddle_threshold={:.2f}",
                avg_pnl,
                win_rate * 100,
                self.bandit.exploration_rate,
                self.straddle_confidence_threshold
            )
            logger.info(
                "Feedback loop: adjusting exploration {:.2f}->{:.2f}, straddle_threshold {:.2f}->{:.2f}",
                old_exploration,
                self.bandit.exploration_rate,
                old_straddle,
                self.straddle_confidence_threshold
            )
        elif avg_pnl > 0 and win_rate > 0.55:
            old_exploration = self.bandit.exploration_rate
            old_straddle = self.straddle_confidence_threshold
            self.bandit.exploration_rate = min(0.25, self.bandit.exploration_rate + 0.05)
            self.straddle_confidence_threshold = max(0.5, self.straddle_confidence_threshold - 0.05)
            logger.info(
                "Feedback loop: strong performance (avg_pnl={:.2f}, win_rate={:.1f}%). "
                "Exploration={:.2f}, straddle_threshold={:.2f}",
                avg_pnl,
                win_rate * 100,
                self.bandit.exploration_rate,
                self.straddle_confidence_threshold
            )
            logger.info(
                "Feedback loop: adjusting exploration {:.2f}->{:.2f}, straddle_threshold {:.2f}->{:.2f}",
                old_exploration,
                self.bandit.exploration_rate,
                old_straddle,
                self.straddle_confidence_threshold
            )
        else:
            logger.info(
                "Feedback loop: stable performance (avg_pnl={:.2f}, win_rate={:.1f}%). No adjustments.",
                avg_pnl,
                win_rate * 100
            )

    def _export_results(self):
        """Export all SDM results."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs('reports/sdm', exist_ok=True)

            # Export learning history
            self.learning_engine.export_learning_history(f'reports/sdm/learning_{timestamp}.json')

            # Export ethics violations
            self.ethics_engine.export_violations(f'reports/sdm/ethics_{timestamp}.json')

            logger.info("SDM results exported")
        except Exception as e:
            logger.error(f"Error exporting SDM results: {e}")


def main():
    """Main entry point for SDM Trading Engine."""
    engine = SDMTradingEngine(
        initial_capital=1000.0,
        update_interval=300  # 5 minutes
    )
    engine.start()


if __name__ == '__main__':
    main()
