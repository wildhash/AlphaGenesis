"""
AlphaGenesis Trading Engine - DeepSeek Strategy Implementation

This is the main trading engine that integrates:
1. DeepSeek Reasoner for disciplined decision making
2. Multi-timeframe confluence analysis
3. Market regime detection
4. Risk management with circuit breaker
5. WEEX API for execution

Based on DeepSeek's Alpha Arena success: 130%+ returns in 10 days
"""

import os
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Optional, Any
import numpy as np
from loguru import logger

# AlphaGenesis imports
from alphagenesis.ai import DeepSeekReasoner, TradeAction
from alphagenesis.data import WEEXClient
from alphagenesis.features import (
    FeatureEngineer,
    MarketRegimeDetector,
    MultiTimeframeConfluence,
    TechnicalIndicators
)
from alphagenesis.risk import RiskManager
from alphagenesis.risk.circuit_breaker import CircuitBreaker


class AlphaGenesisEngine:
    """
    Main trading engine implementing DeepSeek's winning strategy.
    
    Key principles:
    - Low frequency trading (max 3 trades/day)
    - Long holds (minimum 4 hours)
    - High risk-reward (minimum 3:1)
    - Multi-timeframe confluence required
    - Strong trend regimes only
    """
    
    # Trading pairs to monitor
    SYMBOLS = ['cmt_btcusdt', 'cmt_ethusdt']
    
    # Timeframes for analysis
    TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d']

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        initial_capital: float = 1000.0,
        max_leverage: float = 15.0,
        update_interval: int = 300,  # 5 minutes
    ):
        """
        Initialize the AlphaGenesis trading engine.
        
        Args:
            api_key: WEEX API key
            api_secret: WEEX API secret
            api_passphrase: WEEX API passphrase
            initial_capital: Starting capital in USDT
            max_leverage: Maximum leverage (capped at 20 for hackathon)
            update_interval: Seconds between market checks
        """
        self.initial_capital = initial_capital
        self.max_leverage = min(max_leverage, 20.0)  # Hackathon cap
        self.update_interval = update_interval
        
        # Initialize WEEX client
        self.weex = WEEXClient(
            api_key=api_key or os.getenv('WEEX_API_KEY'),
            api_secret=api_secret or os.getenv('WEEX_API_SECRET'),
            api_passphrase=api_passphrase or os.getenv('WEEX_API_PASSPHRASE')
        )
        
        # Initialize DeepSeek Reasoner (THE KEY COMPONENT)
        self.reasoner = DeepSeekReasoner(
            min_confluence=0.7,
            min_risk_reward=3.0,
            max_leverage=self.max_leverage,
            min_hold_hours=4,
            max_daily_trades=3
        )
        
        # Initialize analysis components
        self.regime_detector = MarketRegimeDetector()
        self.confluence_analyzer = MultiTimeframeConfluence(timeframes=['1h', '4h', '1d'])
        self.technical = TechnicalIndicators()
        
        # Risk management
        self.circuit_breaker = CircuitBreaker(
            max_leverage=self.max_leverage,
            max_daily_drawdown=0.10,
            max_total_drawdown=0.25
        )
        
        # State
        self.is_running = False
        self.positions: Dict[str, Any] = {}
        self.equity_history = []
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"AlphaGenesis Engine initialized - Capital: ${initial_capital}, Max Leverage: {self.max_leverage}x")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.warning(f"Received signal {signum}, initiating shutdown...")
        self.stop()

    def start(self):
        """Start the trading engine."""
        logger.info("="*60)
        logger.info("ALPHAGENESIS ENGINE STARTING")
        logger.info("="*60)
        logger.info(f"Strategy: DeepSeek Alpha Arena Winner")
        logger.info(f"Max Daily Trades: 3")
        logger.info(f"Min Risk-Reward: 3:1")
        logger.info(f"Min Confluence: 70%")
        logger.info("="*60)
        
        self.is_running = True
        self._run_loop()
    
    def stop(self):
        """Stop the trading engine."""
        logger.info("Stopping AlphaGenesis Engine...")
        self.is_running = False
        self._close_all_positions()
        self._export_results()
        logger.info("Engine stopped.")
    
    def _run_loop(self):
        """Main trading loop."""
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                timestamp = datetime.now()
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {iteration} - {timestamp}")
                logger.info(f"{'='*60}")
                
                # Check circuit breaker
                if self.circuit_breaker.is_tripped:
                    logger.warning("Circuit breaker tripped - trading paused")
                    time.sleep(self.update_interval)
                    continue
                
                # Get current account state
                account = self._get_account_state()
                
                # Process each symbol
                for symbol in self.SYMBOLS:
                    self._process_symbol(symbol, account)
                
                # Log status
                self._log_status(account)
                
                # Sleep until next iteration
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a bit on error

    def _process_symbol(self, symbol: str, account: Dict):
        """
        Process a single symbol through the full analysis pipeline.
        
        Pipeline:
        1. Fetch multi-timeframe data
        2. Detect market regime
        3. Calculate confluence
        4. Generate signal from models
        5. Pass through DeepSeek Reasoner
        6. Execute if approved
        """
        try:
            logger.info(f"\nAnalyzing {symbol}...")
            
            # Step 1: Fetch data for all timeframes
            price_data = self._fetch_multi_timeframe_data(symbol)
            if not price_data:
                logger.warning(f"Could not fetch data for {symbol}")
                return
            
            # Step 2: Detect market regime (using 1h data)
            prices_1h = price_data.get('1h', [])
            if len(prices_1h) < 50:
                logger.warning(f"Insufficient 1h data for {symbol}")
                return
            
            regime = self.regime_detector.detect_regime(np.array(prices_1h))
            logger.info(f"Regime: {regime.regime.value} (confidence: {regime.confidence:.2f})")
            
            # Step 3: Calculate multi-timeframe confluence
            confluence = self.confluence_analyzer.calculate_confluence(price_data)
            logger.info(f"Confluence: {confluence.confluence_score:.2f} - {confluence.recommendation}")
            
            # Step 4: Generate signal (simplified - would use ML models in production)
            signal = self._generate_signal(price_data, regime, confluence)
            
            if signal['direction'] == 'HOLD':
                logger.info(f"No actionable signal for {symbol}")
                return
            
            # Step 5: Build market context for reasoner
            current_price = float(prices_1h[-1])
            atr = self._calculate_atr(prices_1h)
            
            market_context = {
                'current_price': current_price,
                'atr': atr,
                'prices_1h': prices_1h,
                'prices_4h': price_data.get('4h', []),
                'prices_1d': price_data.get('1d', []),
                'funding_rate': self._get_funding_rate(symbol),
                'account_balance': account.get('balance', self.initial_capital)
            }
            
            # Step 6: Pass through DeepSeek Reasoner (THE GATEKEEPER)
            decision = self.reasoner.evaluate_trade_signal(
                symbol=symbol,
                proposed_signal=signal,
                market_context=market_context
            )
            
            # Log the reasoning chain
            logger.info(f"\n{decision.reasoning_summary}")
            
            # Step 7: Execute if approved
            if decision.is_trade:
                self._execute_trade(symbol, decision)
            else:
                logger.info(f"Trade rejected by DeepSeek Reasoner")
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    def _fetch_multi_timeframe_data(self, symbol: str) -> Dict[str, list]:
        """Fetch price data for all timeframes."""
        data = {}
        
        for tf in self.TIMEFRAMES:
            try:
                candles = self.weex.get_candles(symbol=symbol, interval=tf.upper(), limit=200)

                # Parse candles - handle both dict and list formats
                closes = []
                if isinstance(candles, dict) and 'data' in candles:
                    candle_data = candles['data']
                elif isinstance(candles, list):
                    candle_data = candles
                else:
                    candle_data = []

                # Extract close prices from each candle
                for c in candle_data:
                    if isinstance(c, dict):
                        closes.append(float(c.get('close', 0)))
                    elif isinstance(c, list) and len(c) >= 5:
                        closes.append(float(c[4]))  # close at index 4

                if closes:
                    data[tf] = closes
            except Exception as e:
                logger.warning(f"Error fetching {tf} data: {e}")
        
        return data
    
    def _generate_signal(
        self, 
        price_data: Dict, 
        regime, 
        confluence
    ) -> Dict[str, Any]:
        """
        Generate trading signal based on regime and confluence.
        
        In production, this would integrate ML model predictions.
        """
        # Simple signal based on regime and confluence
        if not self.regime_detector.is_tradeable(regime):
            return {'direction': 'HOLD', 'confidence': 0.0, 'leverage': 0.0}
        
        if not self.confluence_analyzer.is_tradeable(confluence):
            return {'direction': 'HOLD', 'confidence': 0.0, 'leverage': 0.0}
        
        # Determine direction
        bias = self.confluence_analyzer.get_trade_bias(confluence)
        
        if bias == 'HOLD':
            return {'direction': 'HOLD', 'confidence': 0.0, 'leverage': 0.0}
        
        # Calculate confidence from confluence and regime
        confidence = (confluence.confluence_score + regime.confidence) / 2
        
        # Suggest leverage based on confidence
        suggested_leverage = min(5 + (confidence * 10), self.max_leverage)
        
        return {
            'direction': bias,
            'confidence': confidence,
            'leverage': suggested_leverage
        }
    
    def _calculate_atr(self, prices: list, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(prices) < period + 1:
            return prices[-1] * 0.02  # Default 2%
        
        prices = np.array(prices)
        highs = prices  # Simplified - using closes as proxy
        lows = prices
        closes = prices
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        atr = np.mean(tr[-period:])
        return atr
    
    def _get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate for perpetuals."""
        # Placeholder - would fetch from API
        return 0.0001  # Default small positive

    def _execute_trade(self, symbol: str, decision):
        """Execute a trade approved by the DeepSeek Reasoner."""
        try:
            logger.info(f"\n{'*'*40}")
            logger.info(f"EXECUTING TRADE: {decision.action.value} {symbol}")
            logger.info(f"Entry: ${decision.entry_price:.2f}")
            logger.info(f"Stop Loss: ${decision.stop_loss:.2f}")
            logger.info(f"Take Profit: ${decision.take_profit:.2f}")
            logger.info(f"Leverage: {decision.leverage:.1f}x")
            logger.info(f"Size: {decision.position_size:.6f}")
            logger.info(f"{'*'*40}")
            
            # Map action to WEEX order side
            if decision.action == TradeAction.LONG:
                side = 1  # Open long
            elif decision.action == TradeAction.SHORT:
                side = 2  # Open short
            else:
                logger.warning(f"Unknown action: {decision.action}")
                return
            
            # Place the order
            result = self.weex.place_order(
                symbol=symbol,
                side=side,
                size=decision.position_size,
                is_market=True
            )
            
            if 'order_id' in result or 'client_oid' in result:
                logger.info(f"Order placed successfully: {result}")
                self.positions[symbol] = {
                    'side': decision.action.value,
                    'entry_price': decision.entry_price,
                    'stop_loss': decision.stop_loss,
                    'take_profit': decision.take_profit,
                    'size': decision.position_size,
                    'timestamp': datetime.now()
                }
            else:
                logger.error(f"Order failed: {result}")
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}", exc_info=True)
    
    def _get_account_state(self) -> Dict:
        """Get current account state."""
        try:
            account = self.weex.get_account()
            balance = self.weex.get_account_balance()
            return {
                'balance': balance,
                'account': account
            }
        except Exception as e:
            logger.error(f"Error fetching account: {e}")
            return {'balance': self.initial_capital}
    
    def _close_all_positions(self):
        """Close all open positions on shutdown."""
        logger.info("Closing all positions...")
        for symbol, pos in self.positions.items():
            try:
                side = 3 if pos['side'] == 'LONG' else 4  # Close opposite
                self.weex.place_order(symbol=symbol, side=side, size=pos['size'], is_market=True)
                logger.info(f"Closed {symbol} position")
            except Exception as e:
                logger.error(f"Error closing {symbol}: {e}")
    
    def _log_status(self, account: Dict):
        """Log current trading status."""
        balance = account.get('balance', self.initial_capital)
        pnl = balance - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        
        stats = self.reasoner.get_decision_stats()
        
        logger.info(f"\n{'='*40}")
        logger.info("STATUS REPORT")
        logger.info(f"{'='*40}")
        logger.info(f"Balance: ${balance:,.2f}")
        logger.info(f"P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"Open Positions: {len(self.positions)}")
        logger.info(f"Trades Today: {stats['trades_today']}")
        logger.info(f"Total Evaluations: {stats['total_evaluations']}")
        logger.info(f"Trade Rate: {stats['trade_rate']:.1%}")
        logger.info(f"{'='*40}\n")
    
    def _export_results(self):
        """Export trading results and reasoning log."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.reasoner.export_reasoning_log(f'reports/reasoning_{timestamp}.json')
            logger.info("Results exported")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")


def main():
    """Main entry point."""
    engine = AlphaGenesisEngine(
        initial_capital=1000.0,
        max_leverage=15.0,
        update_interval=300  # 5 minutes
    )
    engine.start()


if __name__ == '__main__':
    main()
