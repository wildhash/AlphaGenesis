"""
Event-Driven Backtester

Implements an event-driven backtesting framework for realistic
simulation of trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from loguru import logger


class Order:
    """Represents a trading order."""
    
    def __init__(
        self,
        symbol: str,
        order_type: str,
        quantity: float,
        side: str,
        price: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.symbol = symbol
        self.order_type = order_type  # 'market' or 'limit'
        self.quantity = quantity
        self.side = side  # 'buy' or 'sell'
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.status = "pending"
        self.filled_price = None
        self.filled_quantity = 0.0


class Position:
    """Represents a trading position."""
    
    def __init__(self, symbol: str, quantity: float, entry_price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = entry_price
    
    def update_price(self, price: float):
        """Update current price."""
        self.current_price = price
    
    def pnl(self) -> float:
        """Calculate position P&L."""
        return (self.current_price - self.entry_price) * self.quantity
    
    def pnl_percent(self) -> float:
        """Calculate position P&L percentage."""
        return ((self.current_price - self.entry_price) / self.entry_price) * 100


class Backtester:
    """
    Event-driven backtesting engine.
    
    Simulates realistic trading with proper order execution, slippage,
    and transaction costs.
    
    Attributes:
        initial_capital: Starting capital
        commission_rate: Commission rate per trade
        slippage_rate: Slippage rate per trade
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
    ):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate (fraction)
            slippage_rate: Slippage rate (fraction)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        # Trading state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        logger.info(f"Backtester initialized with capital: {initial_capital}")
    
    def reset(self):
        """Reset backtester to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.orders = []
        self.trades = []
        self.equity_curve = []
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> Order:
        """
        Place a trading order.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: 'market' or 'limit'
            price: Limit price (for limit orders)
            timestamp: Order timestamp
            
        Returns:
            Order object
        """
        order = Order(symbol, order_type, quantity, side, price, timestamp)
        self.orders.append(order)
        logger.debug(f"Order placed: {side} {quantity} {symbol} @ {order_type}")
        return order
    
    def execute_order(self, order: Order, current_price: float) -> bool:
        """
        Execute an order at current market conditions.
        
        Args:
            order: Order to execute
            current_price: Current market price
            
        Returns:
            True if order was executed
        """
        if order.status != "pending":
            return False
        
        # Check if limit order can be filled
        if order.order_type == "limit":
            if order.side == "buy" and current_price > order.price:
                return False
            if order.side == "sell" and current_price < order.price:
                return False
        
        # Calculate execution price with slippage
        if order.side == "buy":
            execution_price = current_price * (1 + self.slippage_rate)
        else:
            execution_price = current_price * (1 - self.slippage_rate)
        
        # Calculate costs
        trade_value = execution_price * order.quantity
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission if order.side == "buy" else trade_value - commission
        
        # Check if we have enough cash for buy orders
        if order.side == "buy" and total_cost > self.cash:
            logger.warning(f"Insufficient cash for order: {order.symbol}")
            order.status = "rejected"
            return False
        
        # Update positions
        if order.side == "buy":
            self.cash -= total_cost
            if order.symbol in self.positions:
                # Add to existing position (average price)
                pos = self.positions[order.symbol]
                total_quantity = pos.quantity + order.quantity
                avg_price = (
                    (pos.entry_price * pos.quantity + execution_price * order.quantity)
                    / total_quantity
                )
                pos.quantity = total_quantity
                pos.entry_price = avg_price
            else:
                self.positions[order.symbol] = Position(
                    order.symbol, order.quantity, execution_price
                )
        
        else:  # sell
            if order.symbol not in self.positions:
                logger.warning(f"Cannot sell: no position in {order.symbol}")
                order.status = "rejected"
                return False
            
            pos = self.positions[order.symbol]
            if order.quantity > pos.quantity:
                logger.warning(f"Cannot sell: insufficient quantity in {order.symbol}")
                order.status = "rejected"
                return False
            
            self.cash += total_cost
            pos.quantity -= order.quantity
            
            # Remove position if fully closed
            if pos.quantity == 0:
                del self.positions[order.symbol]
        
        # Record trade
        order.status = "filled"
        order.filled_price = execution_price
        order.filled_quantity = order.quantity
        
        self.trades.append({
            "timestamp": order.timestamp,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": execution_price,
            "commission": commission,
        })
        
        logger.debug(
            f"Order executed: {order.side} {order.quantity} {order.symbol} "
            f"@ {execution_price:.2f}"
        )
        
        return True
    
    def update_equity(self, timestamp: datetime, prices: Dict[str, float]):
        """
        Update equity curve with current portfolio value.
        
        Args:
            timestamp: Current timestamp
            prices: Dictionary of current prices for each symbol
        """
        # Update position prices
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.update_price(prices[symbol])
        
        # Calculate total equity
        positions_value = sum(pos.quantity * pos.current_price for pos in self.positions.values())
        total_equity = self.cash + positions_value
        
        self.equity_curve.append({
            "timestamp": timestamp,
            "cash": self.cash,
            "positions_value": positions_value,
            "total_equity": total_equity,
        })
    
    def run(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        symbol: str = "BTC/USDT",
    ) -> pd.DataFrame:
        """
        Run backtest on historical data.
        
        Args:
            data: Historical market data
            strategy_func: Strategy function that generates signals
            symbol: Trading symbol
            
        Returns:
            DataFrame with backtest results
        """
        self.reset()
        
        logger.info(f"Starting backtest on {len(data)} data points")
        
        for idx, row in data.iterrows():
            timestamp = idx if isinstance(idx, datetime) else datetime.now()
            current_price = row["close"]
            
            # Generate trading signal
            signal = strategy_func(data.loc[:idx])
            
            # Execute strategy logic
            if signal == "buy" and symbol not in self.positions:
                # Calculate position size (simple: use 90% of cash)
                quantity = (self.cash * 0.9) / current_price
                self.place_order(symbol, "buy", quantity, timestamp=timestamp)
            
            elif signal == "sell" and symbol in self.positions:
                quantity = self.positions[symbol].quantity
                self.place_order(symbol, "sell", quantity, timestamp=timestamp)
            
            # Execute pending orders
            for order in self.orders:
                if order.status == "pending":
                    self.execute_order(order, current_price)
            
            # Update equity
            self.update_equity(timestamp, {symbol: current_price})
        
        logger.info(f"Backtest completed: {len(self.trades)} trades executed")
        
        return pd.DataFrame(self.equity_curve)
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get backtest results summary.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        final_equity = equity_df["total_equity"].iloc[-1]
        
        returns = equity_df["total_equity"].pct_change().dropna()
        
        results = {
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return": (final_equity - self.initial_capital) / self.initial_capital,
            "total_return_pct": ((final_equity - self.initial_capital) / self.initial_capital) * 100,
            "total_trades": len(self.trades),
            "mean_return": returns.mean(),
            "std_return": returns.std(),
            "sharpe_ratio": returns.mean() / returns.std() if returns.std() > 0 else 0,
            "max_equity": equity_df["total_equity"].max(),
            "min_equity": equity_df["total_equity"].min(),
        }
        
        return results
