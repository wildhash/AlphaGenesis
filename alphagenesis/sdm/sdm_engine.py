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
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import numpy as np
from loguru import logger

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
from alphagenesis.models import LSTMModel, TransformerModel, EnsemblePredictor
from alphagenesis.risk import RiskManager
from alphagenesis.risk.circuit_breaker import CircuitBreaker
from alphagenesis.risk.risk_manager_veto import RiskManagerVeto, AccountState, TradeIntent, VetoReason
from alphagenesis.execution.position_ledger import PositionLedger
from alphagenesis.execution.position_monitor import PositionMonitor
from alphagenesis.execution.breakout_straddle import BreakoutStraddleManager
from alphagenesis.learning import DecisionJournal, DecisionTick, TradeEvent, ContextualBanditAllocator


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
        self.risk_manager = RiskManagerVeto(
            initial_balance=initial_capital,
            max_notional_per_symbol=2000.0,
            max_total_notional=5000.0,
            max_leverage=15.0,
            max_margin_ratio=0.80,
            max_daily_loss_pct=0.10,
            max_total_drawdown_pct=0.25,
            max_per_trade_risk_pct=0.01,  # 1% per trade (conservative)
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
            poll_interval_seconds=30
        )
        logger.info("✓ Position Monitor initialized - will start with engine")

        # DRY RUN MODE
        self.dry_run_mode = os.getenv('DRY_RUN', 'false').lower() == 'true'
        if self.dry_run_mode:
            logger.warning("🟡 DRY RUN MODE ACTIVE - No real orders will be placed")

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
            dry_run=self.dry_run_mode
        )
        self.straddle_confidence_threshold = 0.55
        self._straddle_tick_seen = set()

        # State
        self.is_running = False
        self.positions: Dict[str, Any] = {}
        self.iteration = 0
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
        self.btc_only_period = 72 * 3600
        self.btc_base_balance = None
        self.gamma_squeeze_active = False
        self.last_margin_used = 0.0
        self.last_unrealized_pnl = 0.0
        self.last_total_notional = 0.0
        self._warned_pnl_field = False
        self._warned_leverage_field = False

        # Aggressive straddle controls (competition tuning)
        self.stop_new_if_pnl_under = -0.06
        self.emergency_stop_at = -0.08

        # Symbol prioritization
        self.priority_symbols = ["cmt_btcusdt"]
        self.secondary_symbols = ["cmt_ethusdt", "cmt_solusdt"]
        self.max_active_symbols = 1
        self.active_symbols = ["cmt_btcusdt"]

        # Symbols to trade (all approved WEEX AI Wars pairs)
        self.symbols = [
            'cmt_btcusdt',
            'cmt_ethusdt',
            'cmt_solusdt',
            'cmt_dogeusdt',
            'cmt_xrpusdt',
            'cmt_adausdt',
            'cmt_bnbusdt',
            'cmt_ltcusdt'
        ]

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
                                legacy_amount=self.legacy_amount
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
        ]
        for key in keys:
            if key in pos and pos[key] is not None:
                try:
                    return float(pos[key])
                except (TypeError, ValueError):
                    continue

        if not self._warned_pnl_field:
            logger.warning(
                "⚠️ Could not find unrealized P&L field in position. Available keys: %s",
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

    def _calculate_position_metrics(self, account: Dict[str, Any]) -> tuple[float, float, float]:
        unrealized_pnl = 0.0
        margin_used = 0.0
        total_notional = 0.0

        positions = account.get('position', [])
        if not isinstance(positions, list):
            return unrealized_pnl, margin_used, total_notional

        for pos in positions:
            try:
                size = float(pos.get('size', 0) or 0)
            except (TypeError, ValueError):
                size = 0.0
            if size == 0:
                continue

            unrealized_pnl += self._extract_unrealized_pnl(pos)

            try:
                notional = float(pos.get('open_value', 0) or 0)
            except (TypeError, ValueError):
                notional = 0.0

            if notional == 0.0:
                mark_price = self._extract_mark_price(pos)
                if mark_price > 0:
                    notional = abs(size) * mark_price

            total_notional += notional

            try:
                leverage = float(pos.get('leverage', 20) or 20)
            except (TypeError, ValueError):
                leverage = 20.0
            if leverage <= 0:
                if not self._warned_leverage_field:
                    logger.warning("⚠️ Invalid leverage on position; defaulting to 20x for margin calc")
                    self._warned_leverage_field = True
                leverage = 20.0
            margin_used += notional / leverage

        return unrealized_pnl, margin_used, total_notional

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
            balance = self.weex.get_account_balance()
            unrealized_pnl, margin_used, total_notional = self._calculate_position_metrics(account)
            equity = balance + unrealized_pnl
            market_state['account'] = {
                'balance': balance,
                'equity': equity,
                'unrealized_pnl': unrealized_pnl,
                'margin_used': margin_used,
                'total_notional': total_notional,
                'daily_pnl': self.daily_pnl,
                'daily_pnl_percent': self.daily_pnl_percent,
                'pnl': equity - self.initial_capital
            }
            self.current_capital = equity
            self.legacy_amount = balance

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
            self._update_symbol_selection(balance)
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
                            self.straddle_manager.update(symbol, price)
                    except Exception as e:
                        logger.warning(f"Straddle update failed for {symbol}: {e}")
                    self._straddle_tick_seen.add(symbol)

                if self.straddle_manager.is_blocked(symbol):
                    logger.info(f"⏸ STRADDLE ACTIVE - skipping normal strategy for {symbol}")
                    continue

                # Determine market regime
                regime = self._detect_regime_for_symbol(symbol)

                # Bind intent to model via semantic binding
                context = {
                    'regime': regime,
                    'symbol': symbol,
                    'balance': market_state['account'].get('balance', self.current_capital)
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

                if not proposed_action or proposed_action.get('direction') == 'HOLD':
                    continue

                self._augment_action_with_risk_metrics(proposed_action)

                # Evaluate action against intent graph
                should_execute, reasoning = self.intent_graph.should_execute_action(proposed_action)

                if not should_execute:
                    logger.info(f"Intent graph rejected: {reasoning}")
                    self._log_straddle_signal_debug(
                        symbol=symbol,
                        action=proposed_action,
                        intent_graph_blocked=True
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
                logger.error(f"Error resolving intent for {symbol}: {e}", exc_info=True)

    def _detect_regime_for_symbol(self, symbol: str) -> MarketRegime:
        """Detect market regime for a symbol."""
        try:
            # Fetch recent candles
            candles = self.weex.get_candles(symbol=symbol, interval='1H', limit=100)

            if not candles:
                return MarketRegime.UNKNOWN

            # Extract closes - handle both dict and list formats
            closes = []
            if isinstance(candles, dict) and 'data' in candles:
                # Response wrapped in 'data' key
                data = candles['data']
            elif isinstance(candles, list):
                # Direct list response
                data = candles
            else:
                return MarketRegime.UNKNOWN

            # Parse individual candles
            for c in data:
                if isinstance(c, dict):
                    # Dictionary format: {'close': value, ...}
                    closes.append(float(c.get('close', 0)))
                elif isinstance(c, list) and len(c) >= 5:
                    # Array format: [timestamp, open, high, low, close, volume]
                    closes.append(float(c[4]))  # close is at index 4

            if len(closes) < 50:
                return MarketRegime.UNKNOWN

            # Simple regime detection
            prices = np.array(closes)
            returns = np.diff(prices) / prices[:-1]
            trend = np.mean(returns[-20:])
            volatility = np.std(returns[-20:])

            # Map to regime
            if abs(trend) < 0.001:
                return MarketRegime.SIDEWAYS
            elif trend > 0.002:
                return MarketRegime.STRONG_UPTREND
            elif trend > 0:
                return MarketRegime.WEAK_UPTREND
            elif trend < -0.002:
                return MarketRegime.STRONG_DOWNTREND
            elif trend < 0:
                return MarketRegime.WEAK_DOWNTREND

            if volatility > 0.02:
                return MarketRegime.HIGH_VOLATILITY
            elif volatility < 0.005:
                return MarketRegime.LOW_VOLATILITY

            return MarketRegime.UNKNOWN

        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return MarketRegime.UNKNOWN

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
        # Get current price
        try:
            ticker = self.weex.get_ticker(symbol)
            if 'data' in ticker:
                price = float(ticker['data'].get('last', 0))
            else:
                price = float(ticker.get('last', 0))
        except:
            return None

        # Fetch candles for strategy
        try:
            candles = self.weex.get_candles(symbol=symbol, interval='1H', limit=100)
        except:
            return None

        # PHASE 2: Bandit selects strategy
        regime_str = regime.value if hasattr(regime, 'value') else str(regime)
        chosen_strategy = self.bandit.select_strategy(symbol, regime_str)

        logger.debug(f"Bandit selected strategy: {chosen_strategy} for {symbol} in {regime_str}")

        # Generate signal using chosen strategy
        if chosen_strategy == 'flat':
            # Bandit learned best action is no action
            return {'direction': 'HOLD', 'confidence': 0.0, 'strategy': 'flat'}
        elif chosen_strategy == 'momentum':
            signal = self.momentum_strategy.generate_signal(candles, price, symbol)
        else:
            # Fallback to momentum if strategy not implemented yet
            signal = self.momentum_strategy.generate_signal(candles, price, symbol)
            chosen_strategy = 'momentum'

        if not signal:
            return {'direction': 'HOLD', 'confidence': 0.0}

        # Position sizing - ULTRA-CONSERVATIVE for margin constraints
        # Use 1% of capital per trade to ensure orders FILL
        position_size_pct = 0.03  # Micro-positions to fit available margin
        position_value = context['balance'] * position_size_pct
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

        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        stop_loss_pct = signal.get('stop_loss_pct')
        take_profit_pct = signal.get('take_profit_pct')
        if stop_loss is None and stop_loss_pct:
            if signal['direction'] == 'LONG':
                stop_loss = price * (1 - stop_loss_pct)
            else:
                stop_loss = price * (1 + stop_loss_pct)
        if take_profit is None and take_profit_pct:
            if signal['direction'] == 'LONG':
                take_profit = price * (1 + take_profit_pct)
            else:
                take_profit = price * (1 - take_profit_pct)

        return {
            'symbol': symbol,
            'direction': signal['direction'],
            'confidence': signal['confidence'],
            'entry_price': price,
            'position_size': size,
            'max_leverage': 15.0,
            'risk_reward_ratio': 3.0,
            'reason': signal.get('reason', ''),
            'strategy': chosen_strategy,
            'regime': regime_str,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            # Features for journal
            'features': features
        }

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

            self._log_straddle_signal_debug(
                symbol=symbol,
                action=action,
                intent_graph_blocked=False
            )

            if self.straddle_manager.is_blocked(symbol):
                logger.info(f"⏸ STRADDLE ACTIVE - skipping execution for {symbol}")
                return

            if action.get('confidence', 0.0) >= self.straddle_confidence_threshold:
                opened = self.straddle_manager.try_open(
                    symbol=symbol,
                    price=action.get('entry_price', 0.0),
                    legacy_amount=self.legacy_amount
                )
                if opened:
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
                # Calculate gross notional exposure
                total_notional = getattr(self, 'last_total_notional', 0.0)
                trade_notional = action['position_size'] * action['entry_price']
                new_gross_notional = total_notional + trade_notional
                gross_exposure_pct = new_gross_notional / self.current_capital if self.current_capital > 0 else 0.0

                # HARD CAP: 30% gross exposure
                MAX_GROSS_EXPOSURE_PCT = 0.30

                if gross_exposure_pct > MAX_GROSS_EXPOSURE_PCT:
                    gross_exposure_blocked = True
                    gross_exposure_reason = (
                        f"GROSS EXPOSURE CAP EXCEEDED: {gross_exposure_pct:.1%} > {MAX_GROSS_EXPOSURE_PCT:.1%} "
                        f"(current: ${total_notional:.2f}, new trade: ${trade_notional:.2f}, "
                        f"total: ${new_gross_notional:.2f}, balance: ${self.current_capital:.2f})"
                    )
                    logger.error(f"❌ {gross_exposure_reason}")

            # === STEP 3: Risk Manager Veto ===
            risk_approved = True
            veto_reasons = []

            if ledger_approved and not gross_exposure_blocked:  # Only check risk if ledger passed AND under gross cap
                # Build account state with REAL values from market observation
                margin_used = getattr(self, 'last_margin_used', 0.0)
                unrealized_pnl = getattr(self, 'last_unrealized_pnl', 0.0)
                total_notional = getattr(self, 'last_total_notional', 0.0)

                account_state = AccountState(
                    balance=self.current_capital,
                    equity=self.current_capital,
                    margin_used=margin_used,
                    unrealized_pnl=unrealized_pnl,
                    daily_pnl=self.daily_pnl,
                    peak_balance_today=self.peak_balance_today,
                    total_notional=total_notional
                )

                risk_approved, veto_reasons = self.risk_manager.approve(
                    trade_intent,
                    account_state,
                    self.position_ledger.get_all_positions()
                )

                if not risk_approved:
                    logger.error(f"❌ RISK VETO: {[v.message for v in veto_reasons]}")

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

                success = 'order_id' in result or 'client_oid' in result

                # DRY_RUN success override (from bug fix)
                if isinstance(result, dict) and result.get('dry_run'):
                    logger.info(f"🟡 DRY_RUN simulated order accepted: {result.get('request', {})}")
                    success = True

                if success:
                    order_id = result.get('order_id') or result.get('client_oid')
                    client_order_id = result.get('client_oid')

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
                # Record in position ledger
                position_recorded = self.position_ledger.open_position(
                    symbol=symbol,
                    side=action['direction'],
                    size=action['position_size'],
                    entry_price=action['entry_price'],
                    client_order_id=client_order_id,
                    order_id=order_id
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
            "📡 SIGNAL DEBUG: %s | Action: %s | Confidence: %.2f | Threshold: %.2f | Active Straddles: %d | "
            "Blocked by Intent Graph: %s",
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
                "📈 VOLATILITY: %s ATR ratio: %.2f | Normal volatility: %s",
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
            account = self.weex.get_account()

            if 'position' not in account:
                logger.info("No positions on exchange to reconcile")
                return True

            active_straddles = set()
            if hasattr(self, 'straddle_manager'):
                active_straddles = self.straddle_manager.active_symbols()

            # Convert WEEX positions to ledger format
            exchange_positions = []
            for pos in account['position']:
                if pos.get('symbol') in active_straddles:
                    continue
                size = float(pos.get('size', 0))
                if size > 0:  # Only active positions
                    # Handle both numeric (1/2) and string ("LONG"/"SHORT") side formats
                    side_value = pos.get('side', 1)
                    if isinstance(side_value, str):
                        # String format: "LONG", "SHORT", "long", "short"
                        side_str = side_value.upper()
                    else:
                        # Numeric format: 1=LONG, 2=SHORT
                        side_num = int(side_value)
                        side_str = 'LONG' if side_num == 1 else 'SHORT'

                    exchange_positions.append({
                        'symbol': pos['symbol'],
                        'side': side_str,
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
        try:
            account = self.weex.get_account()
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
                    "⚠️ GAMMA SQUEEZE DETECTED: %s | Accel: %.2f%% | Volume: %.1fx",
                    symbol,
                    recent_return * 100,
                    volume_ratio
                )
            return gamma_squeeze
        except Exception as e:
            logger.warning(f"Gamma squeeze detection failed for {symbol}: {e}")
            return False

    def _log_sdm_status(self):
        """Log SDM system status."""
        pnl = self.current_capital - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100

        logger.info(f"\n{'='*70}")
        logger.info("SDM SYSTEM STATUS")
        logger.info(f"{'='*70}")
        logger.info(f"Capital: ${self.current_capital:,.2f} (P&L: ${pnl:+,.2f} / {pnl_pct:+.2f}%)")
        logger.info(f"Daily Trades: {self.daily_trades}")

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
