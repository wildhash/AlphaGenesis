"""
WEEX Exchange API Client - Updated for AI Wars Hackathon

Provides a comprehensive interface to the WEEX exchange API for:
- Market data retrieval (OHLCV, order book, trades)
- Account information and balance queries
- Order placement, modification, and cancellation
- Futures trading with leverage

Updated: December 2025
API Base: https://api-contract.weex.com
"""

import os
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from loguru import logger


class WEEXClient:
    """
    Client for interacting with WEEX Futures API.
    
    Handles authentication, rate limiting, and provides methods for
    accessing market data and executing trades.
    """
    
    # API Endpoints (validated via API test on 2025-12-27)
    BASE_URL = "https://api-contract.weex.com"
    
    # Public endpoints
    TICKER_ENDPOINT = "/capi/v2/market/ticker"
    CANDLES_ENDPOINT = "/capi/v2/market/candles"
    ORDERBOOK_ENDPOINT = "/capi/v2/market/depth"
    
    # Private endpoints
    ACCOUNTS_ENDPOINT = "/capi/v2/account/accounts"
    POSITION_ENDPOINT = "/capi/v2/account/position/singlePosition"
    SET_LEVERAGE_ENDPOINT = "/capi/v2/account/setLeverage"
    PLACE_ORDER_ENDPOINT = "/capi/v2/order/placeOrder"
    CANCEL_ORDER_ENDPOINT = "/capi/v2/order/cancel"
    CURRENT_ORDERS_ENDPOINT = "/capi/v2/order/current"
    ORDER_HISTORY_ENDPOINT = "/capi/v2/order/history"
    TRADE_FILLS_ENDPOINT = "/capi/v2/order/fills"

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
            base_url: Base API URL
        """
        self.api_key = api_key or os.getenv("WEEX_API_KEY")
        self.api_secret = api_secret or os.getenv("WEEX_API_SECRET")
        self.api_passphrase = api_passphrase or os.getenv("WEEX_API_PASSPHRASE")
        self.base_url = base_url or self.BASE_URL
        
        if not all([self.api_key, self.api_secret, self.api_passphrase]):
            logger.warning("WEEX API credentials not fully configured")
        else:
            logger.info("WEEX API client initialized with credentials")
    
    def _generate_signature(
        self, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        query_string: str = "",
        body: str = ""
    ) -> str:
        """
        Generate HMAC-SHA256 signature for API request.
        
        Signature format: timestamp + method + requestPath + queryString + body
        """
        message = timestamp + method.upper() + request_path + query_string + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _get_headers(
        self, 
        method: str, 
        endpoint: str, 
        query_string: str = "",
        body: str = ""
    ) -> Dict[str, str]:
        """Generate authenticated headers for request."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, endpoint, query_string, body)
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.api_passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }

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
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            signed: Whether request requires authentication
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        query_string = ""
        body = ""
        
        if params:
            query_string = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        if data:
            body = json.dumps(data)
        
        if signed:
            headers = self._get_headers(method, endpoint, query_string, body)
        else:
            headers = {"Content-Type": "application/json", "locale": "en-US"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url + query_string, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=body, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.debug(f"API {method} {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WEEX API request failed: {e}")
            raise
    
    # =========================================================================
    # PUBLIC MARKET DATA ENDPOINTS
    # =========================================================================
    
    def get_ticker(self, symbol: str = "cmt_btcusdt") -> Dict[str, Any]:
        """
        Get current ticker for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'cmt_btcusdt')
            
        Returns:
            Ticker data with last price, bid, ask, volume, etc.
        """
        return self._request("GET", self.TICKER_ENDPOINT, params={"symbol": symbol})

    def get_candles(
        self, 
        symbol: str = "cmt_btcusdt",
        interval: str = "1H",
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        Get historical candlestick data.
        
        Args:
            symbol: Trading pair
            interval: Candle interval (1m, 5m, 15m, 1H, 4H, 1D)
            limit: Number of candles (max 1000)
            
        Returns:
            List of OHLCV candles
        """
        params = {
            "symbol": symbol,
            "period": interval,
            "limit": limit
        }
        return self._request("GET", self.CANDLES_ENDPOINT, params=params)
    
    def get_orderbook(self, symbol: str = "cmt_btcusdt", limit: int = 20) -> Dict[str, Any]:
        """
        Get current order book.
        
        Args:
            symbol: Trading pair
            limit: Depth level
            
        Returns:
            Order book with bids and asks
        """
        params = {"symbol": symbol, "limit": limit}
        return self._request("GET", self.ORDERBOOK_ENDPOINT, params=params)
    
    # =========================================================================
    # PRIVATE ACCOUNT ENDPOINTS
    # =========================================================================
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information including balance.
        
        Returns:
            Account data with collateral and positions
        """
        return self._request("GET", self.ACCOUNTS_ENDPOINT, signed=True)
    
    def get_position(self, symbol: str = "cmt_btcusdt") -> Dict[str, Any]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Position data
        """
        params = {"symbol": symbol}
        return self._request("GET", self.POSITION_ENDPOINT, params=params, signed=True)
    
    def set_leverage(
        self, 
        symbol: str = "cmt_btcusdt",
        leverage: int = 10,
        side: int = 1,
        hold_side: str = "long"
    ) -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair
            leverage: Leverage multiplier (1-125, but we cap at 20 for hackathon)
            side: 1 = isolated, 2 = cross
            hold_side: 'long' or 'short'
            
        Returns:
            Leverage setting result
        """
        # Enforce hackathon 20x cap
        leverage = min(leverage, 20)
        
        data = {
            "symbol": symbol,
            "leverage": str(leverage),
            "side": str(side),
            "holdSide": hold_side
        }
        return self._request("POST", self.SET_LEVERAGE_ENDPOINT, data=data, signed=True)

    # =========================================================================
    # PRIVATE ORDER ENDPOINTS
    # =========================================================================
    
    def place_order(
        self,
        symbol: str,
        side: int,
        size: float,
        price: float = 0,
        order_type: str = "0",
        is_market: bool = True,
        client_oid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a futures order.
        
        Args:
            symbol: Trading pair (e.g., 'cmt_btcusdt')
            side: 1=open long, 2=open short, 3=close long, 4=close short
            size: Order size in base currency (BTC)
            price: Limit price (ignored for market orders)
            order_type: "0"=normal, "1"=post only, "2"=FOK, "3"=IOC
            is_market: True for market order, False for limit
            client_oid: Optional client order ID
            
        Returns:
            Order placement result with order_id
        """
        if client_oid is None:
            client_oid = f"{int(time.time() * 1000)}{os.urandom(4).hex()}"
        
        data = {
            "symbol": symbol,
            "client_oid": client_oid,
            "size": str(size),
            "type": str(side),
            "order_type": order_type,
            "match_price": "1" if is_market else "0",
            "price": str(price)
        }
        
        logger.info(f"Placing order: {data}")
        return self._request("POST", self.PLACE_ORDER_ENDPOINT, data=data, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an open order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        data = {"symbol": symbol, "orderId": order_id}
        return self._request("POST", self.CANCEL_ORDER_ENDPOINT, data=data, signed=True)
    
    def get_open_orders(self, symbol: str = "cmt_btcusdt") -> Dict[str, Any]:
        """
        Get all open orders for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            List of open orders
        """
        params = {"symbol": symbol}
        return self._request("GET", self.CURRENT_ORDERS_ENDPOINT, params=params, signed=True)
    
    def get_order_history(
        self, 
        symbol: str = "cmt_btcusdt",
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get order history.
        
        Args:
            symbol: Trading pair
            page_size: Number of orders to return
            
        Returns:
            List of historical orders
        """
        params = {"symbol": symbol, "pageSize": page_size}
        return self._request("GET", self.ORDER_HISTORY_ENDPOINT, params=params, signed=True)
    
    def get_trade_fills(
        self, 
        symbol: str = "cmt_btcusdt",
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get trade fill details.
        
        Args:
            symbol: Trading pair
            page_size: Number of fills to return
            
        Returns:
            List of trade fills with P&L
        """
        params = {"symbol": symbol, "pageSize": page_size}
        return self._request("GET", self.TRADE_FILLS_ENDPOINT, params=params, signed=True)

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    def get_btc_price(self) -> float:
        """Get current BTC/USDT price."""
        ticker = self.get_ticker("cmt_btcusdt")
        if "last" in ticker:
            return float(ticker["last"])
        elif "data" in ticker and "last" in ticker["data"]:
            return float(ticker["data"]["last"])
        raise ValueError(f"Could not parse price from ticker: {ticker}")
    
    def get_eth_price(self) -> float:
        """Get current ETH/USDT price."""
        ticker = self.get_ticker("cmt_ethusdt")
        if "last" in ticker:
            return float(ticker["last"])
        elif "data" in ticker and "last" in ticker["data"]:
            return float(ticker["data"]["last"])
        raise ValueError(f"Could not parse price from ticker: {ticker}")
    
    def get_account_balance(self) -> float:
        """Get USDT balance."""
        account = self.get_account()
        if "collateral" in account:
            for c in account["collateral"]:
                if c.get("coin_id") == 2:  # USDT
                    return float(c.get("amount", 0))
        return 0.0
    
    def open_long(self, symbol: str, size: float, is_market: bool = True) -> Dict:
        """Open a long position."""
        return self.place_order(symbol, side=1, size=size, is_market=is_market)
    
    def close_long(self, symbol: str, size: float, is_market: bool = True) -> Dict:
        """Close a long position."""
        return self.place_order(symbol, side=3, size=size, is_market=is_market)
    
    def open_short(self, symbol: str, size: float, is_market: bool = True) -> Dict:
        """Open a short position."""
        return self.place_order(symbol, side=2, size=size, is_market=is_market)
    
    def close_short(self, symbol: str, size: float, is_market: bool = True) -> Dict:
        """Close a short position."""
        return self.place_order(symbol, side=4, size=size, is_market=is_market)


# Quick test function
def test_client():
    """Test the WEEX client with real API."""
    client = WEEXClient(
        api_key=os.getenv("WEEX_API_KEY"),
        api_secret=os.getenv("WEEX_API_SECRET"),
        api_passphrase=os.getenv("WEEX_API_PASSPHRASE")
    )
    
    # Test public endpoint
    ticker = client.get_ticker()
    print(f"BTC Price: ${ticker.get('last', ticker.get('data', {}).get('last', 'N/A'))}")
    
    # Test private endpoint
    account = client.get_account()
    print(f"Account: {account}")
    
    return client


if __name__ == "__main__":
    test_client()
