"""
AlphaGenesis Trading System - Main Entry Point

Coordinates all components for live trading:
- Multi-agent decision making
- Risk management
- Order execution
- Performance monitoring
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, Optional
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alphagenesis.agents import MultiAgentTradingSystem
from alphagenesis.risk.quantum_risk_manager import QuantumRiskManager
from alphagenesis.features.multi_source_feature_engineer import MultiSourceFeatureEngineer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alphagenesis_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlphaGenesisTradingSystem:
    """
    Main trading system orchestrator.
    
    Coordinates all components:
    - Multi-agent decision making
    - Feature engineering
    - Risk management
    - Order execution
    """
    
    def __init__(
        self,
        initial_capital: float = 10000,
        paper_trading: bool = True,
        enable_all_agents: bool = True
    ):
        """
        Initialize trading system.
        
        Args:
            initial_capital: Starting capital
            paper_trading: Use paper trading mode
            enable_all_agents: Enable all trading agents
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.paper_trading = paper_trading
        
        logger.info("Initializing AlphaGenesis Trading System...")
        logger.info(f"Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"Mode: {'Paper Trading' if paper_trading else 'LIVE TRADING'}")
        
        # Initialize components
        self.multi_agent_system = MultiAgentTradingSystem(
            enable_scalper=enable_all_agents,
            enable_swing=enable_all_agents,
            enable_arbitrage=enable_all_agents,
            enable_market_maker=False  # Disabled by default
        )
        
        self.risk_manager = QuantumRiskManager(
            initial_capital=initial_capital,
            max_risk_per_trade=0.02,
            max_total_risk=0.10
        )
        
        self.feature_engineer = MultiSourceFeatureEngineer()
        
        # Trading state
        self.positions = {}
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0
        }
        
        logger.info("✓ Trading system initialized successfully")
    
    def run(
        self,
        symbols: list = None,
        duration_minutes: int = 60,
        update_interval: int = 60
    ):
        """
        Run the trading system.
        
        Args:
            symbols: List of trading symbols
            duration_minutes: How long to run (0 = indefinite)
            update_interval: Update interval in seconds
        """
        symbols = symbols or ['BTC/USDT', 'ETH/USDT']
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 STARTING ALPHAGENESIS TRADING SYSTEM")
        logger.info("=" * 60)
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Update Interval: {update_interval}s")
        logger.info(f"Duration: {'Indefinite' if duration_minutes == 0 else f'{duration_minutes} minutes'}")
        logger.info("=" * 60)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                iteration_start = time.time()
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Process each symbol
                for symbol in symbols:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                
                # Display performance summary
                self._display_performance_summary()
                
                # Check if duration exceeded
                if duration_minutes > 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"Duration of {duration_minutes} minutes reached. Stopping...")
                        break
                
                # Wait for next iteration
                iteration_duration = time.time() - iteration_start
                sleep_time = max(0, update_interval - iteration_duration)
                
                if sleep_time > 0:
                    logger.info(f"Sleeping for {sleep_time:.1f}s until next iteration...")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt received. Shutting down...")
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}", exc_info=True)
        finally:
            self._shutdown()
    
    def _process_symbol(self, symbol: str):
        """Process a single trading symbol."""
        logger.info(f"\n--- Processing {symbol} ---")
        
        # Step 1: Create market state (simplified)
        market_state = self._create_market_state(symbol)
        
        # Step 2: Get multi-agent decision
        logger.info("Getting multi-agent decision...")
        consensus_decision = self.multi_agent_system.decide(market_state)
        
        logger.info(f"Consensus: {consensus_decision.action} "
                   f"(confidence: {consensus_decision.confidence:.2%})")
        logger.info(f"Participating agents: {len(consensus_decision.participating_agents)}")
        
        # Step 3: Apply risk management
        if consensus_decision.action != 'HOLD' and consensus_decision.confidence > 0.6:
            position_rec = self.risk_manager.calculate_position_size(
                signal_confidence=consensus_decision.confidence,
                current_price=market_state.get('close', 50000),
                volatility=market_state.get('volatility', 0.02),
                market_regime=market_state.get('regime', 'neutral')
            )
            
            logger.info(f"Risk Manager Recommendation:")
            logger.info(f"  Position Size: {position_rec.size:.2%}")
            logger.info(f"  Stop Loss: ${position_rec.stop_loss:.2f}")
            logger.info(f"  Take Profit: ${position_rec.take_profit:.2f}")
            logger.info(f"  Uncertainty: {position_rec.uncertainty:.2%}")
            
            # Step 4: Execute trade (paper trading)
            if position_rec.size > 0.01:  # Minimum 1% position
                self._execute_trade(
                    symbol=symbol,
                    action=consensus_decision.action,
                    size=position_rec.size,
                    price=market_state.get('close', 50000),
                    stop_loss=position_rec.stop_loss,
                    take_profit=position_rec.take_profit
                )
        else:
            logger.info(f"No trade executed: {consensus_decision.action} "
                       f"(confidence: {consensus_decision.confidence:.2%})")
    
    def _create_market_state(self, symbol: str) -> Dict:
        """Create market state dictionary (simplified)."""
        # In production, would fetch real data
        import numpy as np
        
        return {
            'symbol': symbol,
            'close': np.random.uniform(48000, 52000) if 'BTC' in symbol else np.random.uniform(2800, 3200),
            'volume': np.random.uniform(1000, 10000),
            'volatility': np.random.uniform(0.01, 0.05),
            'trend': np.random.choice(['uptrend', 'downtrend', 'neutral']),
            'momentum': np.random.uniform(-0.02, 0.02),
            'rsi_14': np.random.uniform(30, 70),
            'macd': np.random.uniform(-50, 50),
            'orderbook_order_book_imbalance': np.random.uniform(-0.3, 0.3),
            'orderbook_net_pressure': np.random.uniform(-0.2, 0.2),
            'spread_pct': np.random.uniform(0.0005, 0.002),
            'regime': np.random.choice(['bull', 'bear', 'neutral'])
        }
    
    def _execute_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: float,
        stop_loss: float,
        take_profit: float
    ):
        """Execute a trade (paper trading)."""
        position_value = self.current_capital * size
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'size': size,
            'price': price,
            'value': position_value,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        
        self.trade_history.append(trade)
        self.performance_metrics['total_trades'] += 1
        
        logger.info(f"📊 TRADE EXECUTED (Paper Trading):")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Action: {action}")
        logger.info(f"  Price: ${price:,.2f}")
        logger.info(f"  Position Size: {size:.2%} (${position_value:,.2f})")
        logger.info(f"  Stop Loss: ${stop_loss:,.2f}")
        logger.info(f"  Take Profit: ${take_profit:,.2f}")
    
    def _display_performance_summary(self):
        """Display performance summary."""
        logger.info(f"\n{'='*60}")
        logger.info("📈 PERFORMANCE SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Current Capital: ${self.current_capital:,.2f}")
        logger.info(f"Total Trades: {self.performance_metrics['total_trades']}")
        logger.info(f"Win Rate: N/A (paper trading)")
        logger.info(f"{'='*60}")
    
    def _shutdown(self):
        """Shutdown trading system."""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 SHUTTING DOWN ALPHAGENESIS TRADING SYSTEM")
        logger.info("=" * 60)
        logger.info(f"Final Capital: ${self.current_capital:,.2f}")
        logger.info(f"Total Trades Executed: {self.performance_metrics['total_trades']}")
        logger.info(f"Trade History Saved: {len(self.trade_history)} trades")
        logger.info("=" * 60)
        logger.info("Thank you for using AlphaGenesis!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='AlphaGenesis Trading System')
    parser.add_argument('--capital', type=float, default=10000,
                       help='Initial capital (default: 10000)')
    parser.add_argument('--live', action='store_true',
                       help='Enable live trading (default: paper trading)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Duration in minutes (0 = indefinite)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Update interval in seconds (default: 60)')
    parser.add_argument('--symbols', nargs='+', default=['BTC/USDT', 'ETH/USDT'],
                       help='Trading symbols')
    
    args = parser.parse_args()
    
    # Initialize and run trading system
    system = AlphaGenesisTradingSystem(
        initial_capital=args.capital,
        paper_trading=not args.live,
        enable_all_agents=True
    )
    
    system.run(
        symbols=args.symbols,
        duration_minutes=args.duration,
        update_interval=args.interval
    )


if __name__ == "__main__":
    main()
