"""
Live Trading Event Loop

Main event loop for live trading that connects all modules:
- Data pipeline
- Feature engineering
- ML models
- Risk management
- Order execution
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime
from threading import Thread, Event
import signal
import sys

from loguru import logger
import pandas as pd
import numpy as np

from alphagenesis.data import WEEXClient, DataFetcher
from alphagenesis.data.data_cleaner import DataCleaner
from alphagenesis.features import FeatureEngineer
from alphagenesis.features.orderbook import OrderBookFeatureEngineer
from alphagenesis.features.temporal import TemporalFeatureEngineer
from alphagenesis.models import LSTMModel, EnsemblePredictor
from alphagenesis.risk import RiskManager
from alphagenesis.risk.circuit_breaker import CircuitBreaker
from alphagenesis.risk.position_sizer import PositionSizer
from alphagenesis.execution import OrderExecutor, OrderManager
from alphagenesis.execution.portfolio import Portfolio
from config.settings import settings
from config.constants import Constants


class LiveTradingLoop:
    """
    Main live trading event loop.
    
    Coordinates all system components:
    1. Fetches real-time data
    2. Engineers features
    3. Generates predictions from ML models
    4. Checks risk constraints
    5. Executes trades
    6. Monitors portfolio
    """
    
    def __init__(
        self,
        symbols: list[str],
        timeframe: str = '1h',
        update_interval: int = 60,
    ):
        """
        Initialize LiveTradingLoop.
        
        Args:
            symbols: List of trading symbols
            timeframe: Candlestick timeframe
            update_interval: Seconds between updates
        """
        self.symbols = symbols
        self.timeframe = timeframe
        self.update_interval = update_interval
        
        # Control flags
        self.is_running = False
        self.stop_event = Event()
        
        # Components
        self.weex_client = WEEXClient()
        self.data_fetcher = DataFetcher(self.weex_client)
        self.data_cleaner = DataCleaner()
        
        # Feature engineering
        self.feature_engineer = FeatureEngineer()
        self.orderbook_engineer = OrderBookFeatureEngineer()
        self.temporal_engineer = TemporalFeatureEngineer()
        
        # ML models (placeholder - load your trained models here)
        self.models = {}
        self.ensemble = EnsemblePredictor()
        
        # Risk management
        self.circuit_breaker = CircuitBreaker(
            max_leverage=settings.max_leverage,
            max_daily_drawdown=settings.max_daily_drawdown,
            max_total_drawdown=settings.max_total_drawdown,
        )
        self.position_sizer = PositionSizer(
            max_leverage=settings.max_leverage,
            max_position_size=settings.max_position_size,
        )
        self.risk_manager = RiskManager(
            max_position_size=settings.max_position_size,
            max_leverage=settings.max_leverage,
        )
        
        # Execution
        self.order_executor = OrderExecutor(self.weex_client)
        self.order_manager = OrderManager(self.weex_client)
        self.portfolio = Portfolio(
            initial_capital=settings.initial_capital,
            commission_rate=Constants.DEFAULT_COMMISSION,
            slippage_rate=Constants.DEFAULT_SLIPPAGE,
        )
        
        # Data cache
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(
            f"LiveTradingLoop initialized for {len(symbols)} symbols, "
            f"timeframe={timeframe}, interval={update_interval}s"
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.warning(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def start(self):
        """Start the live trading loop."""
        if self.is_running:
            logger.warning("Trading loop is already running")
            return
        
        logger.info("=" * 60)
        logger.info("STARTING LIVE TRADING")
        logger.info("=" * 60)
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Leverage Cap: {settings.max_leverage}x")
        logger.info(f"Max Daily DD: {settings.max_daily_drawdown:.1%}")
        logger.info(f"Max Total DD: {settings.max_total_drawdown:.1%}")
        logger.info("=" * 60)
        
        # Validate API credentials
        if not settings.validate_api_credentials():
            logger.error("Invalid API credentials, cannot start trading")
            return
        
        self.is_running = True
        
        # Start main loop in separate thread
        self.loop_thread = Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()
        
        logger.info("Live trading loop started")
    
    def stop(self):
        """Stop the live trading loop."""
        if not self.is_running:
            logger.warning("Trading loop is not running")
            return
        
        logger.info("Stopping live trading loop...")
        self.is_running = False
        self.stop_event.set()
        
        # Close all positions
        self._close_all_positions()
        
        # Wait for loop thread to finish
        if hasattr(self, 'loop_thread'):
            self.loop_thread.join(timeout=10)
        
        # Export logs and reports
        self._export_reports()
        
        logger.info("Live trading loop stopped")
    
    def _run_loop(self):
        """Main trading loop."""
        iteration = 0
        
        while self.is_running and not self.stop_event.is_set():
            try:
                iteration += 1
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Iteration {iteration} - {datetime.now()}")
                logger.info(f"{'=' * 60}")
                
                # Check circuit breaker
                if self.circuit_breaker.is_tripped:
                    logger.warning("Circuit breaker is tripped, skipping trading")
                    time.sleep(self.update_interval)
                    continue
                
                # Process each symbol
                for symbol in self.symbols:
                    self._process_symbol(symbol)
                
                # Update portfolio
                self._update_portfolio()
                
                # Log status
                self._log_status()
                
                # Sleep until next iteration
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.update_interval)
        
        logger.info("Main loop exited")
    
    def _process_symbol(self, symbol: str):
        """
        Process a single symbol.
        
        Steps:
        1. Fetch latest data
        2. Engineer features
        3. Generate prediction
        4. Calculate position size
        5. Execute trade if conditions met
        """
        try:
            logger.debug(f"Processing {symbol}...")
            
            # Fetch latest data
            df = self._fetch_data(symbol)
            if df is None or len(df) < 100:
                logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Clean data
            df = self.data_cleaner.clean(df)
            
            # Engineer features
            df = self.feature_engineer.create_features(df)
            df = self.temporal_engineer.create_features(df)
            
            # Get latest features
            latest_features = df.iloc[-1].values
            
            # Generate prediction
            prediction = self._generate_prediction(latest_features, symbol)
            signal_strength = prediction.get('signal', 0.0)
            
            logger.info(f"{symbol} signal: {signal_strength:+.3f}")
            
            # Skip if signal too weak
            if abs(signal_strength) < 0.1:
                logger.debug(f"Signal too weak for {symbol}, skipping")
                return
            
            # Calculate position size
            current_price = df.iloc[-1]['close']
            asset_volatility = df['close'].pct_change().std() * np.sqrt(365 * 24)
            
            size_result = self.position_sizer.calculate_optimal_size(
                signal_strength=signal_strength,
                asset_volatility=asset_volatility,
                account_balance=self.portfolio.get_total_equity(),
            )
            
            position_size = size_result['final_size']
            
            # Check risk constraints
            current_positions = {
                s: self.portfolio.get_position(s)
                for s in self.symbols
                if self.portfolio.get_position(s) is not None
            }
            
            order_check = self.circuit_breaker.check_order(
                order_size=position_size * self.portfolio.get_total_equity() / current_price,
                order_price=current_price,
                current_equity=self.portfolio.get_total_equity(),
                current_positions=current_positions,
            )
            
            if not order_check['allowed']:
                logger.warning(f"Order rejected: {order_check['reason']}")
                return
            
            # Execute trade
            self._execute_trade(symbol, signal_strength, position_size, current_price)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)
    
    def _fetch_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch latest market data for symbol."""
        try:
            df = self.data_fetcher.fetch_ohlcv(
                symbol=symbol,
                interval=self.timeframe,
                limit=200,  # Fetch last 200 candles
            )
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _generate_prediction(self, features: np.ndarray, symbol: str) -> Dict[str, float]:
        """Generate trading signal from ML models."""
        try:
            # If ensemble has models, use it
            if self.ensemble.models:
                result = self.ensemble.predict(features.reshape(1, -1))
                signal = result.get('ensemble', np.array([0.0]))[0]
            else:
                # Default: simple signal (placeholder)
                signal = 0.0
            
            return {'signal': float(signal)}
            
        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {e}")
            return {'signal': 0.0}
    
    def _execute_trade(
        self,
        symbol: str,
        signal: float,
        position_size: float,
        price: float,
    ):
        """Execute trade based on signal."""
        try:
            # Determine action
            current_position = self.portfolio.get_position(symbol)
            
            if signal > 0:
                # Buy signal
                action = "BUY"
                size = position_size * self.portfolio.get_total_equity() / price
            else:
                # Sell signal
                action = "SELL"
                size = position_size * self.portfolio.get_total_equity() / price
            
            logger.info(f"Executing {action} for {symbol}: size={size:.4f}, price={price:.2f}")
            
            # Update portfolio (in live trading, would place real order)
            if signal > 0:
                self.portfolio.open_position(symbol, size, price, datetime.now())
            elif current_position:
                self.portfolio.close_position(symbol, price=price, timestamp=datetime.now())
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
    
    def _update_portfolio(self):
        """Update portfolio with current prices."""
        try:
            prices = {}
            for symbol in self.symbols:
                df = self._fetch_data(symbol)
                if df is not None and len(df) > 0:
                    prices[symbol] = df.iloc[-1]['close']
            
            self.portfolio.update_positions(prices, datetime.now())
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def _close_all_positions(self):
        """Close all open positions."""
        logger.info("Closing all positions...")
        
        for symbol in list(self.portfolio.positions.keys()):
            try:
                df = self._fetch_data(symbol)
                if df is not None and len(df) > 0:
                    price = df.iloc[-1]['close']
                    self.portfolio.close_position(symbol, price=price)
                    logger.info(f"Closed position for {symbol}")
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {e}")
    
    def _log_status(self):
        """Log current trading status."""
        summary = self.portfolio.get_performance_summary()
        
        logger.info(f"\n{'=' * 40}")
        logger.info("PORTFOLIO STATUS")
        logger.info(f"{'=' * 40}")
        logger.info(f"Equity: ${summary['final_equity']:,.2f}")
        logger.info(f"Return: {summary['total_return_pct']:+.2f}%")
        logger.info(f"Positions: {summary['n_positions']}")
        logger.info(f"Total Trades: {summary['n_trades']}")
        logger.info(f"Win Rate: {summary['win_rate'] * 100:.1f}%")
        logger.info(f"Max DD: {summary['max_drawdown_pct']:.2f}%")
        logger.info(f"{'=' * 40}\n")
    
    def _export_reports(self):
        """Export trading reports."""
        try:
            # Export equity curve
            equity_df = self.portfolio.get_equity_curve()
            if len(equity_df) > 0:
                equity_df.to_csv('reports/live_equity_curve.csv')
                logger.info("Exported equity curve")
            
            # Export trades
            trades_df = self.portfolio.get_trades_df()
            if len(trades_df) > 0:
                trades_df.to_csv('reports/live_trades.csv')
                logger.info("Exported trades")
            
            # Export circuit breaker violations
            if len(self.circuit_breaker.violation_log) > 0:
                self.circuit_breaker.export_violation_log('reports/violations.csv')
                logger.info("Exported violations")
            
        except Exception as e:
            logger.error(f"Error exporting reports: {e}")


def main():
    """Main entry point for live trading."""
    # Initialize loop
    loop = LiveTradingLoop(
        symbols=settings.trading_pairs,
        timeframe=settings.default_timeframe,
        update_interval=60,
    )
    
    # Start trading
    loop.start()
    
    # Keep main thread alive
    try:
        while loop.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        loop.stop()


if __name__ == '__main__':
    main()
