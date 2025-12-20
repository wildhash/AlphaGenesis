"""
Order Manager

Manages the lifecycle of trading orders and tracks their status.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from loguru import logger


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ManagedOrder:
    """
    Represents a managed order with tracking capabilities.
    """
    
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ):
        """
        Initialize managed order.
        
        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Order quantity
            price: Order price (for limit orders)
        """
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.filled_price = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.exchange_order_id = None
    
    def update_status(self, status: OrderStatus):
        """Update order status."""
        self.status = status
        self.updated_at = datetime.now()
    
    def update_fill(self, filled_quantity: float, filled_price: float):
        """Update fill information."""
        self.filled_quantity = filled_quantity
        self.filled_price = filled_price
        self.updated_at = datetime.now()
        
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class OrderManager:
    """
    Manages trading orders and tracks their lifecycle.
    
    Provides order tracking, status monitoring, and order history.
    """
    
    def __init__(self):
        """Initialize order manager."""
        self.orders: Dict[str, ManagedOrder] = {}
        self.order_history: List[ManagedOrder] = []
        self._order_counter = 0
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> ManagedOrder:
        """
        Create a new managed order.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: Order quantity
            price: Order price (for limit orders)
            
        Returns:
            ManagedOrder instance
        """
        self._order_counter += 1
        order_id = f"ORDER_{self._order_counter:06d}"
        
        order = ManagedOrder(order_id, symbol, side, order_type, quantity, price)
        self.orders[order_id] = order
        
        logger.info(f"Created order: {order_id} - {side} {quantity} {symbol}")
        return order
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update order status.
        
        Args:
            order_id: Order ID to update
            status: New status
            
        Returns:
            True if update successful
        """
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        order.update_status(status)
        
        logger.debug(f"Order {order_id} status updated to {status.value}")
        
        # Move completed orders to history
        if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            self.order_history.append(order)
            del self.orders[order_id]
        
        return True
    
    def update_order_fill(
        self,
        order_id: str,
        filled_quantity: float,
        filled_price: float,
    ) -> bool:
        """
        Update order fill information.
        
        Args:
            order_id: Order ID to update
            filled_quantity: Quantity filled
            filled_price: Fill price
            
        Returns:
            True if update successful
        """
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        order.update_fill(filled_quantity, filled_price)
        
        logger.info(f"Order {order_id} filled: {filled_quantity} @ {filled_price}")
        
        # Move to history if fully filled
        if order.status == OrderStatus.FILLED:
            self.order_history.append(order)
            del self.orders[order_id]
        
        return True
    
    def get_order(self, order_id: str) -> Optional[ManagedOrder]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            ManagedOrder if found, None otherwise
        """
        # Check active orders
        if order_id in self.orders:
            return self.orders[order_id]
        
        # Check history
        for order in self.order_history:
            if order.order_id == order_id:
                return order
        
        return None
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[ManagedOrder]:
        """
        Get all active orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of active orders
        """
        orders = list(self.orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        return orders
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[ManagedOrder]:
        """
        Get order history.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of orders to return
            
        Returns:
            List of historical orders
        """
        history = self.order_history
        
        if symbol:
            history = [o for o in history if o.symbol == symbol]
        
        return history[-limit:]
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all active orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Number of orders cancelled
        """
        orders_to_cancel = self.get_active_orders(symbol)
        
        for order in orders_to_cancel:
            self.update_order_status(order.order_id, OrderStatus.CANCELLED)
        
        logger.info(f"Cancelled {len(orders_to_cancel)} orders")
        return len(orders_to_cancel)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get order statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_orders = len(self.orders) + len(self.order_history)
        active_orders = len(self.orders)
        
        filled_orders = sum(
            1 for o in self.order_history if o.status == OrderStatus.FILLED
        )
        cancelled_orders = sum(
            1 for o in self.order_history if o.status == OrderStatus.CANCELLED
        )
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
        }
