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
from datetime import datetime
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

        # State
        self.is_running = False
        self.positions: Dict[str, Any] = {}
        self.iteration = 0
        self.total_pnl = 0.0
        self.daily_trades = 0
        self.last_trade_time = None

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
        """Handle shutdown signals."""
        logger.warning(f"Received signal {signum}, initiating shutdown...")
        self.stop()

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
        self._run_dataflow_loop()

    def stop(self):
        """Stop the SDM trading engine."""
        logger.info("Stopping SDM Trading Engine...")
        self.is_running = False
        self._close_all_positions()
        self._export_results()
        logger.info("SDM Engine stopped.")

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

                for intent_node in active_intents:
                    self._resolve_intent(intent_node, market_state)

                # Step 4: Continuous Rebinding (Check if bindings still optimal)
                self.binding_layer.continuous_rebinding()

                # Step 5: Adapt if necessary
                if self.learning_engine.should_adapt():
                    self.learning_engine.adapt(self.intent_graph, self.binding_layer)

                # Step 6: Log status
                self._log_sdm_status()

                # Sleep until next iteration
                time.sleep(self.update_interval)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in dataflow loop: {e}", exc_info=True)
                time.sleep(60)

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
            market_state['account'] = {
                'balance': balance,
                'equity': balance,  # Simplified
                'pnl': balance - self.initial_capital
            }
            self.current_capital = balance
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

        # For each symbol, try to resolve intent
        for symbol in self.symbols:
            try:
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

                # Evaluate action against intent graph
                should_execute, reasoning = self.intent_graph.should_execute_action(proposed_action)

                if not should_execute:
                    logger.info(f"Intent graph rejected: {reasoning}")
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
        Generate a proposed action using momentum strategy.

        Uses proven technical indicators (RSI, MA, momentum) instead of
        untrained ML models for reliable signals.
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

        # Fetch candles for momentum strategy
        try:
            candles = self.weex.get_candles(symbol=symbol, interval='1H', limit=100)
        except:
            return None

        # Generate signal using momentum strategy
        signal = self.momentum_strategy.generate_signal(candles, price, symbol)

        if not signal:
            return {'direction': 'HOLD', 'confidence': 0.0}

        # Position sizing - COMPETITION-OPTIMIZED for many small wins
        # Use 10% of capital per trade with tight stops for high win rate
        position_size_pct = 0.10  # Smaller positions, more trades, tight risk management
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

        return {
            'symbol': symbol,
            'direction': signal['direction'],
            'confidence': signal['confidence'],
            'entry_price': price,
            'position_size': size,
            'max_leverage': 15.0,  # Increased from 10x to 15x
            'risk_reward_ratio': 3.0,
            'reason': signal.get('reason', '')
        }

    def _execute_action(
        self,
        symbol: str,
        action: Dict,
        intent_id: str,
        model_type: ModelType
    ):
        """Execute a trading action."""
        try:
            logger.info(f"\n{'*'*60}")
            logger.info(f"EXECUTING ACTION via SDM")
            logger.info(f"Intent: {intent_id}")
            logger.info(f"Model: {model_type.value}")
            logger.info(f"Symbol: {symbol}")
            logger.info(f"Direction: {action['direction']}")
            logger.info(f"Size: {action.get('position_size', 0):.6f}")
            logger.info(f"Price: ${action.get('entry_price', 0):.2f}")
            logger.info(f"{'*'*60}")

            # Map direction to WEEX side
            if action['direction'] == 'LONG':
                side = 1
            elif action['direction'] == 'SHORT':
                side = 2
            else:
                return

            # Skip if position size is too small after rounding
            if action['position_size'] <= 0:
                logger.warning(f"Position size too small after rounding, skipping trade")
                return

            # Place order
            result = self.weex.place_order(
                symbol=symbol,
                side=side,
                size=action['position_size'],
                is_market=True
            )

            success = 'order_id' in result or 'client_oid' in result

            # Handle insufficient margin errors gracefully
            if not success and 'margin' in str(result).lower():
                logger.warning(f"⚠ Insufficient margin for {symbol}, will try next signal")
                return

            # Record feedback
            feedback = PerformanceFeedback(
                action_id=f"action_{self.iteration}_{symbol}",
                intent_id=intent_id,
                model_type=model_type.value,
                timestamp=datetime.now(),
                success=success,
                pnl=0.0,  # Will be updated when position closes
                fitness_score=action.get('confidence', 0.5),
                context=action
            )

            self.learning_engine.record_feedback(feedback)

            # Record in intent graph
            fitness_scores = self.intent_graph.evaluate_proposed_action(action)
            self.intent_graph.record_action_result(action, success, fitness_scores)

            if success:
                self.daily_trades += 1
                self.last_trade_time = datetime.now()
                logger.info(f"✓ Order placed successfully")
            else:
                logger.error(f"✗ Order failed: {result}")

        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)

    def _close_all_positions(self):
        """Close all open positions."""
        logger.info("Closing all positions...")
        # Implementation similar to legacy engine
        pass

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
