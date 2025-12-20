"""
Portfolio Management Module

Tracks positions, P&L, and equity curve in real-time for live trading and backtesting.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class Position:
    """
    Represents a single trading position.
    """
    symbol: str
    size: float  # Positive for long, negative for short
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def update_price(self, current_price: float):
        """Update current price and calculate unrealized P&L."""
        self.current_price = current_price
        self.unrealized_pnl = (current_price - self.entry_price) * self.size
    
    def close(self, exit_price: float, exit_time: datetime) -> float:
        """
        Close the position and calculate realized P&L.
        
        Returns:
            Realized P&L
        """
        self.realized_pnl = (exit_price - self.entry_price) * self.size
        return self.realized_pnl


@dataclass
class Trade:
    """
    Represents a completed trade.
    """
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    size: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    commission: float = 0.0
    slippage: float = 0.0


class Portfolio:
    """
    Portfolio manager for tracking positions, P&L, and equity curve.
    
    Handles:
    - Position management (open, close, update)
    - P&L calculation (realized and unrealized)
    - Equity curve tracking
    - Trade history
    - Performance metrics
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
    ):
        """
        Initialize Portfolio.
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission as fraction of trade value
            slippage_rate: Slippage as fraction of price
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        # Current state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.equity_history: List[Dict[str, Any]] = []
        self.trade_history: List[Trade] = []
        
        # Performance tracking
        self.total_commission = 0.0
        self.total_slippage = 0.0
        self.peak_equity = initial_capital
        self.max_drawdown = 0.0
        
        logger.info(
            f"Portfolio initialized: capital={initial_capital}, "
            f"commission={commission_rate:.4f}, slippage={slippage_rate:.4f}"
        )
    
    def open_position(
        self,
        symbol: str,
        size: float,
        price: float,
        timestamp: datetime,
    ) -> bool:
        """
        Open a new position or add to existing position.
        
        Args:
            symbol: Trading symbol
            size: Position size (positive for long, negative for short)
            price: Entry price
            timestamp: Entry timestamp
            
        Returns:
            True if successful, False otherwise
        """
        # Calculate costs
        trade_value = abs(size * price)
        commission = trade_value * self.commission_rate
        slippage = trade_value * self.slippage_rate
        total_cost = trade_value + commission + slippage
        
        # Check if enough cash
        if total_cost > self.cash:
            logger.warning(
                f"Insufficient cash for position: required={total_cost:.2f}, "
                f"available={self.cash:.2f}"
            )
            return False
        
        # Create or update position
        if symbol in self.positions:
            # Adding to existing position
            existing = self.positions[symbol]
            
            # Check if same direction
            if np.sign(size) != np.sign(existing.size):
                # Opposite direction - close existing first
                self._close_position_internal(
                    symbol, abs(min(abs(existing.size), abs(size))), price, timestamp
                )
                
                # If there's remaining size, open new position
                remaining_size = abs(size) - abs(existing.size)
                if remaining_size > 0:
                    size = remaining_size * np.sign(size)
                else:
                    return True
            else:
                # Same direction - average in
                total_size = existing.size + size
                avg_price = (
                    (existing.entry_price * existing.size + price * size) / total_size
                )
                existing.size = total_size
                existing.entry_price = avg_price
                existing.current_price = price
                logger.info(
                    f"Added to position {symbol}: new_size={total_size}, "
                    f"avg_price={avg_price:.2f}"
                )
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                size=size,
                entry_price=price,
                entry_time=timestamp,
                current_price=price,
            )
            logger.info(
                f"Opened position {symbol}: size={size}, price={price:.2f}"
            )
        
        # Update cash
        self.cash -= total_cost
        self.total_commission += commission
        self.total_slippage += slippage
        
        return True
    
    def close_position(
        self,
        symbol: str,
        size: Optional[float] = None,
        price: float = 0.0,
        timestamp: Optional[datetime] = None,
    ) -> Optional[float]:
        """
        Close a position (fully or partially).
        
        Args:
            symbol: Trading symbol
            size: Size to close (None = close all)
            price: Exit price
            timestamp: Exit timestamp
            
        Returns:
            Realized P&L or None if position doesn't exist
        """
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return None
        
        timestamp = timestamp or datetime.now()
        position = self.positions[symbol]
        
        # Determine size to close
        close_size = size if size is not None else abs(position.size)
        close_size = min(close_size, abs(position.size))
        
        return self._close_position_internal(symbol, close_size, price, timestamp)
    
    def _close_position_internal(
        self,
        symbol: str,
        close_size: float,
        price: float,
        timestamp: datetime,
    ) -> float:
        """
        Internal method to close position.
        """
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = (price - position.entry_price) * close_size * np.sign(position.size)
        
        # Calculate costs
        trade_value = close_size * price
        commission = trade_value * self.commission_rate
        slippage = trade_value * self.slippage_rate
        
        net_pnl = pnl - commission - slippage
        
        # Update cash
        self.cash += trade_value + net_pnl
        self.total_commission += commission
        self.total_slippage += slippage
        
        # Record trade
        pnl_percent = (pnl / (position.entry_price * close_size)) * 100
        trade = Trade(
            symbol=symbol,
            direction='long' if position.size > 0 else 'short',
            entry_price=position.entry_price,
            exit_price=price,
            size=close_size,
            entry_time=position.entry_time,
            exit_time=timestamp,
            pnl=net_pnl,
            pnl_percent=pnl_percent,
            commission=commission,
            slippage=slippage,
        )
        self.trade_history.append(trade)
        
        # Update or remove position
        if close_size >= abs(position.size):
            # Close entire position
            del self.positions[symbol]
            logger.info(
                f"Closed position {symbol}: pnl={net_pnl:.2f} ({pnl_percent:+.2f}%)"
            )
        else:
            # Partial close
            position.size -= close_size * np.sign(position.size)
            position.realized_pnl += net_pnl
            logger.info(
                f"Partially closed {symbol}: closed={close_size}, "
                f"remaining={abs(position.size)}, pnl={net_pnl:.2f}"
            )
        
        return net_pnl
    
    def update_positions(self, prices: Dict[str, float], timestamp: datetime):
        """
        Update all positions with current prices.
        
        Args:
            prices: Dictionary of symbol -> current_price
            timestamp: Current timestamp
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
        
        # Record equity snapshot
        self._record_equity_snapshot(timestamp)
    
    def _record_equity_snapshot(self, timestamp: datetime):
        """
        Record current equity and positions.
        """
        equity = self.get_total_equity()
        
        snapshot = {
            'timestamp': timestamp,
            'cash': self.cash,
            'equity': equity,
            'n_positions': len(self.positions),
            'unrealized_pnl': self.get_unrealized_pnl(),
        }
        
        self.equity_history.append(snapshot)
        
        # Update peak and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        drawdown = (self.peak_equity - equity) / self.peak_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.
        
        Returns:
            Position object or None
        """
        return self.positions.get(symbol)
    
    def get_unrealized_pnl(self) -> float:
        """
        Get total unrealized P&L across all positions.
        
        Returns:
            Total unrealized P&L
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_realized_pnl(self) -> float:
        """
        Get total realized P&L from closed trades.
        
        Returns:
            Total realized P&L
        """
        return sum(trade.pnl for trade in self.trade_history)
    
    def get_total_equity(self) -> float:
        """
        Get total equity (cash + unrealized P&L).
        
        Returns:
            Total portfolio equity
        """
        return self.cash + self.get_unrealized_pnl()
    
    def get_equity_curve(self) -> pd.DataFrame:
        """
        Get equity curve as DataFrame.
        
        Returns:
            DataFrame with equity history
        """
        if not self.equity_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.equity_history)
        df.set_index('timestamp', inplace=True)
        return df
    
    def get_trades_df(self) -> pd.DataFrame:
        """
        Get trade history as DataFrame.
        
        Returns:
            DataFrame with trade history
        """
        if not self.trade_history:
            return pd.DataFrame()
        
        trades_data = [vars(trade) for trade in self.trade_history]
        return pd.DataFrame(trades_data)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        equity = self.get_total_equity()
        total_return = (equity - self.initial_capital) / self.initial_capital
        
        trades_df = self.get_trades_df()
        
        if len(trades_df) > 0:
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]
            
            win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = abs(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0
            
            profit_factor = (
                abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum())
                if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0
                else float('inf') if len(winning_trades) > 0 else 0
            )
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': equity,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'realized_pnl': self.get_realized_pnl(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'peak_equity': self.peak_equity,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown * 100,
            'n_trades': len(self.trade_history),
            'n_positions': len(self.positions),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_commission': self.total_commission,
            'total_slippage': self.total_slippage,
        }
