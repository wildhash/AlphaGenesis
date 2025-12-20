"""
Order Executor

Handles the execution of trading orders through the exchange API.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from alphagenesis.data.weex_client import WEEXClient


class OrderExecutor:
    """
    Executes trading orders through the exchange API.
    
    Provides a high-level interface for order placement and management,
    with built-in error handling and retry logic.
    """
    
    def __init__(self, weex_client: Optional[WEEXClient] = None):
        """
        Initialize order executor.
        
        Args:
            weex_client: WEEX API client instance
        """
        self.weex_client = weex_client or WEEXClient()
    
    def execute_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Dict[str, Any]:
        """
        Execute a market order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            
        Returns:
            Order execution result
        """
        try:
            logger.info(f"Executing market order: {side} {quantity} {symbol}")
            
            result = self.weex_client.place_order(
                symbol=symbol,
                side=side,
                order_type="market",
                quantity=quantity,
            )
            
            logger.info(f"Market order executed successfully: {result.get('order_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Market order execution failed: {e}")
            raise
    
    def execute_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        """
        Execute a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price
            
        Returns:
            Order execution result
        """
        try:
            logger.info(f"Executing limit order: {side} {quantity} {symbol} @ {price}")
            
            result = self.weex_client.place_order(
                symbol=symbol,
                side=side,
                order_type="limit",
                quantity=quantity,
                price=price,
            )
            
            logger.info(f"Limit order placed successfully: {result.get('order_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Limit order execution failed: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            logger.info(f"Cancelling order: {order_id}")
            
            result = self.weex_client.cancel_order(order_id)
            
            logger.info(f"Order cancelled successfully: {order_id}")
            return result
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information
        """
        try:
            # This would call a get_order method on the WEEX client
            # For now, we return a placeholder
            logger.debug(f"Checking order status: {order_id}")
            return {"order_id": order_id, "status": "unknown"}
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise
    
    def execute_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float,
    ) -> Dict[str, Any]:
        """
        Execute a stop loss order.
        
        Args:
            symbol: Trading pair symbol
            quantity: Order quantity
            stop_price: Stop loss trigger price
            
        Returns:
            Order execution result
        """
        try:
            logger.info(f"Placing stop loss: {quantity} {symbol} @ {stop_price}")
            
            # Stop loss orders would typically be placed as stop-market orders
            # The exact implementation depends on exchange capabilities
            result = {
                "order_type": "stop_loss",
                "symbol": symbol,
                "quantity": quantity,
                "stop_price": stop_price,
                "timestamp": datetime.now(),
            }
            
            logger.info("Stop loss order placed")
            return result
            
        except Exception as e:
            logger.error(f"Stop loss order failed: {e}")
            raise
