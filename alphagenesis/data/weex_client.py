"""
WEEX Exchange API Client

Provides a comprehensive interface to the WEEX exchange API for:
- Market data retrieval (OHLCV, order book, trades)
- Account information and balance queries
- Order placement, modification, and cancellation
- WebSocket connections for real-time data streams
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import hmac
import hashlib
import time
from loguru import logger


class WEEXClient:
    """
    Client for interacting with WEEX exchange API.
    
    Handles authentication, rate limiting, and provides methods for
    accessing market data and executing trades.
    
    Attributes:
        api_key: API key for authentication
        api_secret: API secret for signing requests
        base_url: Base URL for API endpoints
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize WEEX API client.
        
        Args:
            api_key: API key (defaults to WEEX_API_KEY env var)
            api_secret: API secret (defaults to WEEX_API_SECRET env var)
            api_passphrase: API passphrase (defaults to WEEX_API_PASSPHRASE env var)
            base_url: Base API URL (defaults to WEEX_BASE_URL env var)
        """
        self.api_key = api_key or os.getenv("WEEX_API_KEY")
        self.api_secret = api_secret or os.getenv("WEEX_API_SECRET")
        self.api_passphrase = api_passphrase or os.getenv("WEEX_API_PASSPHRASE")
        self.base_url = base_url or os.getenv("WEEX_BASE_URL", "https://api.weex.com")
        
        if not all([self.api_key, self.api_secret]):
            logger.warning("WEEX API credentials not fully configured")
    
    def _generate_signature(self, timestamp: str, method: str, endpoint: str, body: str = "") -> str:
        """
        Generate HMAC signature for API request.
        
        Args:
            timestamp: Request timestamp
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            body: Request body (for POST requests)
            
        Returns:
            HMAC signature string
        """
        message = f"{timestamp}{method}{endpoint}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WEEX API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            signed: Whether request requires authentication
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if signed:
            timestamp = str(int(time.time() * 1000))
            body = "" if data is None else str(data)
            signature = self._generate_signature(timestamp, method, endpoint, body)
            
            headers.update({
                "WEEX-API-KEY": self.api_key,
                "WEEX-TIMESTAMP": timestamp,
                "WEEX-SIGN": signature,
                "WEEX-PASSPHRASE": self.api_passphrase,
            })
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WEEX API request failed: {e}")
            raise
    
    def get_market_data(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical OHLCV market data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            interval: Candlestick interval (1m, 5m, 1h, 1d, etc.)
            limit: Number of data points to retrieve
            
        Returns:
            List of OHLCV candlestick data
        """
        endpoint = "/api/v1/market/candles"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        return self._request("GET", endpoint, params=params)
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Retrieve current order book for a symbol.
        
        Args:
            symbol: Trading pair symbol
            depth: Order book depth (number of price levels)
            
        Returns:
            Order book data with bids and asks
        """
        endpoint = "/api/v1/market/orderbook"
        params = {"symbol": symbol, "depth": depth}
        return self._request("GET", endpoint, params=params)
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Retrieve account balance information.
        
        Returns:
            Account balance data
        """
        endpoint = "/api/v1/account/balance"
        return self._request("GET", endpoint, signed=True)
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            order_type: Order type ('limit', 'market')
            quantity: Order quantity
            price: Order price (required for limit orders)
            
        Returns:
            Order placement response
        """
        endpoint = "/api/v1/orders"
        data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if price is not None:
            data["price"] = price
        
        return self._request("POST", endpoint, data=data, signed=True)
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
        """
        endpoint = f"/api/v1/orders/{order_id}"
        return self._request("DELETE", endpoint, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all open orders.
        
        Args:
            symbol: Optional symbol to filter orders
            
        Returns:
            List of open orders
        """
        endpoint = "/api/v1/orders/open"
        params = {"symbol": symbol} if symbol else {}
        return self._request("GET", endpoint, params=params, signed=True)
