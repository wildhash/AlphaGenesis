"""
Backtest Runner Script

Runs a complete backtest of the AlphaGenesis trading system with configurable parameters.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenesis.data import WEEXClient, DataFetcher
from alphagenesis.data.data_cleaner import DataCleaner
from alphagenesis.features import FeatureEngineer
from alphagenesis.features.technical_indicators import TechnicalIndicators
from alphagenesis.features.orderbook import OrderBookFeatureEngineer
from alphagenesis.features.temporal import TemporalFeatureEngineer
from alphagenesis.models import LSTMModel
from alphagenesis.risk import RiskManager, VaRCalculator
from alphagenesis.risk.circuit_breaker import CircuitBreaker
from alphagenesis.risk.position_sizer import PositionSizer
from alphagenesis.backtest import Backtester, PerformanceMetrics
from alphagenesis.execution.portfolio import Portfolio
from config.settings import settings
from config.constants import Constants
from loguru import logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run AlphaGenesis backtest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        default='BTC/USDT',
        help='Trading pair to backtest'
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1h',
        help='Candlestick timeframe'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        help='Backtest start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Backtest end date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=100000.0,
        help='Initial capital for backtest'
    )
    
    parser.add_argument(
        '--max-leverage',
        type=float,
        default=20.0,
        help='Maximum leverage (hackathon cap: 20x)'
    )
    
    parser.add_argument(
        '--commission',
        type=float,
        default=Constants.DEFAULT_COMMISSION,
        help='Commission rate'
    )
    
    parser.add_argument(
        '--slippage',
        type=float,
        default=Constants.DEFAULT_SLIPPAGE,
        help='Slippage rate'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./reports',
        help='Output directory for reports'
    )
    
    parser.add_argument(
        '--use-cached-data',
        action='store_true',
        help='Use cached data if available'
    )
    
    return parser.parse_args()


def simple_strategy(df, position_sizer, risk_manager):
    """
    Simple example strategy for demonstration.
    
    Uses RSI for signals and position sizing from risk engine.
    """
    signals = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Simple RSI strategy
        if 'rsi' in row:
            rsi = row['rsi']
            
            if rsi < 30:
                # Oversold - buy signal
                signal_strength = (30 - rsi) / 30  # 0-1 scale
                signals.append(signal_strength)
            elif rsi > 70:
                # Overbought - sell signal
                signal_strength = -(rsi - 70) / 30  # -1 to 0 scale
                signals.append(signal_strength)
            else:
                # Neutral
                signals.append(0.0)
        else:
            signals.append(0.0)
    
    df['signal'] = signals
    return df


def main():
    """Main backtest execution."""
    args = parse_args()
    
    logger.info("=" * 60)
    logger.info("AlphaGenesis Backtest Runner")
    logger.info("=" * 60)
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    logger.info(f"Initial Capital: ${args.initial_capital:,.2f}")
    logger.info(f"Max Leverage: {args.max_leverage}x")
    logger.info("=" * 60)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    logger.info("Initializing components...")
    
    weex_client = WEEXClient()
    data_fetcher = DataFetcher(weex_client)
    data_cleaner = DataCleaner()
    
    # Fetch data
    logger.info(f"Fetching market data for {args.symbol}...")
    df = data_fetcher.fetch_ohlcv(
        symbol=args.symbol,
        interval=args.timeframe,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    
    if df is None or len(df) == 0:
        logger.error("Failed to fetch data")
        return 1
    
    logger.info(f"Fetched {len(df)} candles")
    
    # Clean data
    logger.info("Cleaning data...")
    df = data_cleaner.clean(df)
    
    # Engineer features
    logger.info("Engineering features...")
    feature_engineer = FeatureEngineer()
    df = feature_engineer.create_features(df)
    
    # Add temporal features
    temporal_engineer = TemporalFeatureEngineer()
    df = temporal_engineer.create_features(df)
    
    logger.info(f"Features created: {len(df.columns)} columns")
    
    # Initialize risk components
    logger.info("Initializing risk management...")
    
    circuit_breaker = CircuitBreaker(
        max_leverage=args.max_leverage,
        max_daily_drawdown=Constants.MAX_DAILY_DRAWDOWN,
        max_total_drawdown=Constants.MAX_TOTAL_DRAWDOWN,
    )
    
    position_sizer = PositionSizer(
        max_leverage=args.max_leverage,
        target_volatility=Constants.TARGET_VOLATILITY,
    )
    
    risk_manager = RiskManager(
        max_position_size=Constants.MAX_POSITION_SIZE,
        max_leverage=args.max_leverage,
    )
    
    # Generate strategy signals
    logger.info("Generating strategy signals...")
    df = simple_strategy(df, position_sizer, risk_manager)
    
    # Initialize portfolio and backtester
    logger.info("Running backtest...")
    
    portfolio = Portfolio(
        initial_capital=args.initial_capital,
        commission_rate=args.commission,
        slippage_rate=args.slippage,
    )
    
    backtester = Backtester(
        initial_capital=args.initial_capital,
        commission_rate=args.commission,
        slippage_rate=args.slippage,
    )
    
    # Run backtest with simple strategy
    results = backtester.run(df, symbol=args.symbol)
    
    # Calculate performance metrics
    logger.info("Calculating performance metrics...")
    metrics = PerformanceMetrics.calculate_all_metrics(results['equity_curve'])
    
    # Display results
    logger.info("=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Return: {metrics.get('total_return', 0) * 100:.2f}%")
    logger.info(f"Annual Return: {metrics.get('annual_return', 0) * 100:.2f}%")
    logger.info(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"Max Drawdown: {metrics.get('max_drawdown', 0) * 100:.2f}%")
    logger.info(f"Win Rate: {metrics.get('win_rate', 0) * 100:.2f}%")
    logger.info(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    logger.info(f"Total Trades: {metrics.get('num_trades', 0)}")
    logger.info("=" * 60)
    
    # Save results
    report_file = output_dir / f"backtest_{args.symbol.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results['equity_curve'].to_csv(report_file)
    logger.info(f"Report saved to: {report_file}")
    
    # Check circuit breaker status
    breaker_status = circuit_breaker.get_status()
    if breaker_status['is_tripped']:
        logger.warning(f"⚠️  Circuit breaker was tripped: {breaker_status['trip_reason']}")
    
    if breaker_status['violations_count'] > 0:
        logger.warning(f"⚠️  {breaker_status['violations_count']} risk violations logged")
        
        # Export violations
        violations_file = output_dir / f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        circuit_breaker.export_violation_log(str(violations_file))
    
    logger.info("Backtest complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
