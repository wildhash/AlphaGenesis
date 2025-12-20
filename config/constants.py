"""
Constants Module

Trading constants including slippage assumptions, fee structure, and market parameters.
"""

from typing import Dict


class Constants:
    """
    Trading constants and market parameters.
    
    Based on WEEX exchange specifications and industry best practices.
    """
    
    # Commission and Slippage (WEEX specific)
    MAKER_FEE = 0.0002  # 0.02% maker fee
    TAKER_FEE = 0.0005  # 0.05% taker fee
    DEFAULT_COMMISSION = 0.001  # 0.1% default (conservative)
    
    # Slippage assumptions (basis points)
    SLIPPAGE_BPS_MIN = 5  # 0.05% minimum slippage
    SLIPPAGE_BPS_MAX = 10  # 0.10% maximum slippage
    DEFAULT_SLIPPAGE = 0.0005  # 0.05% default
    
    # Leverage and Position Sizing
    MAX_LEVERAGE = 20.0  # WEEX AI Wars Hackathon cap
    MIN_LEVERAGE = 1.0
    DEFAULT_LEVERAGE = 3.0
    
    # Risk Parameters
    MAX_DAILY_DRAWDOWN = 0.10  # 10% daily drawdown limit
    MAX_TOTAL_DRAWDOWN = 0.25  # 25% total drawdown limit
    MAX_POSITION_SIZE = 0.30  # 30% of portfolio per position
    MIN_POSITION_SIZE = 0.01  # 1% minimum position
    
    # Kelly Criterion
    KELLY_FRACTION = 0.25  # Use 25% of full Kelly (conservative)
    MAX_KELLY_POSITION = 0.20  # Cap Kelly at 20% of portfolio
    
    # Volatility Targeting
    TARGET_VOLATILITY = 0.15  # 15% annualized volatility target
    MIN_VOLATILITY = 0.05  # 5% minimum volatility
    MAX_VOLATILITY = 0.50  # 50% maximum volatility
    
    # Time Constants
    TRADING_DAYS_PER_YEAR = 365  # Crypto trades 24/7
    HOURS_PER_DAY = 24
    MINUTES_PER_HOUR = 60
    SECONDS_PER_MINUTE = 60
    
    # Annualization factors
    ANNUAL_FACTOR_DAILY = 365
    ANNUAL_FACTOR_HOURLY = 365 * 24
    ANNUAL_FACTOR_MINUTELY = 365 * 24 * 60
    
    # Market Parameters
    MARKET_IMPACT_COEFFICIENT = 0.001  # 0.1% market impact per 1% of volume
    MIN_LIQUIDITY_RATIO = 0.01  # Minimum order size as % of volume
    
    # Order Types
    ORDER_TYPE_MARKET = "market"
    ORDER_TYPE_LIMIT = "limit"
    ORDER_TYPE_STOP = "stop"
    ORDER_TYPE_STOP_LIMIT = "stop_limit"
    
    # Position Sides
    SIDE_LONG = "long"
    SIDE_SHORT = "short"
    SIDE_NEUTRAL = "neutral"
    
    # Model Parameters
    LSTM_SEQUENCE_LENGTH = 100  # 100 time steps as specified
    TRANSFORMER_SEQUENCE_LENGTH = 100
    LOOKBACK_PERIODS = {
        '1m': 1440,  # 1 day of 1-minute candles
        '5m': 288,   # 1 day of 5-minute candles
        '15m': 96,   # 1 day of 15-minute candles
        '1h': 168,   # 1 week of hourly candles
        '4h': 180,   # 1 month of 4-hour candles
        '1d': 365,   # 1 year of daily candles
    }
    
    # Feature Engineering
    RSI_PERIOD = 14
    ATR_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2.0
    
    # Technical Indicator Bounds
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_MIN = 0
    RSI_MAX = 100
    
    # GARCH Parameters
    GARCH_P = 1  # GARCH lag order
    GARCH_Q = 1  # ARCH lag order
    GARCH_MEAN_MODEL = "Constant"
    GARCH_VOL_MODEL = "GARCH"
    GARCH_DIST = "normal"
    
    # VaR Parameters
    VAR_CONFIDENCE_LEVEL = 0.95  # 95% confidence
    VAR_HORIZON_DAYS = 1  # 1-day VaR
    VAR_SIMULATION_PATHS = 10000  # Monte Carlo simulations
    
    # Backtesting
    INITIAL_CAPITAL = 100000.0  # $100K initial capital
    MIN_CAPITAL = 10000.0  # Minimum capital to continue trading
    BACKTEST_WARMUP_PERIODS = 200  # Periods for indicator warmup
    
    # Performance Metrics
    RISK_FREE_RATE = 0.02  # 2% annual risk-free rate
    MIN_SHARPE_RATIO = 1.0  # Minimum acceptable Sharpe ratio
    TARGET_SHARPE_RATIO = 2.0  # Target Sharpe ratio
    
    # Circuit Breaker
    CIRCUIT_BREAKER_COOLDOWN_MINUTES = 60  # 1 hour cooldown
    MAX_HOURLY_LOSS = 0.05  # 5% max loss per hour
    MAX_CONSECUTIVE_LOSSES = 5  # Max consecutive losing trades
    
    # Data Quality
    MAX_MISSING_DATA_PCT = 0.05  # 5% max missing data
    OUTLIER_STD_THRESHOLD = 5.0  # 5 std dev for outlier detection
    MAX_FILL_GAP = 5  # Max consecutive NaN to fill
    
    # API Rate Limits (WEEX)
    API_RATE_LIMIT_PER_SECOND = 10
    API_RATE_LIMIT_PER_MINUTE = 600
    API_MAX_RETRIES = 3
    API_RETRY_DELAY = 1.0  # seconds
    
    # WebSocket
    WS_RECONNECT_DELAY = 5  # seconds
    WS_MAX_RECONNECTS = 10
    WS_PING_INTERVAL = 30  # seconds
    
    # Logging
    LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_ROTATION = "100 MB"
    LOG_RETENTION = "30 days"
    
    # File Formats
    DATA_FORMAT_PARQUET = "parquet"
    DATA_FORMAT_CSV = "csv"
    DATA_FORMAT_HDF5 = "hdf5"
    DEFAULT_DATA_FORMAT = DATA_FORMAT_PARQUET
    
    @classmethod
    def get_commission_for_pair(cls, pair: str, is_maker: bool = False) -> float:
        """
        Get commission rate for a trading pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            is_maker: Whether this is a maker order
            
        Returns:
            Commission rate
        """
        # Could be pair-specific in the future
        return cls.MAKER_FEE if is_maker else cls.TAKER_FEE
    
    @classmethod
    def get_slippage_for_pair(cls, pair: str, volatility: float = 0.0) -> float:
        """
        Get slippage estimate for a trading pair.
        
        Args:
            pair: Trading pair
            volatility: Current volatility (used for dynamic adjustment)
            
        Returns:
            Slippage rate
        """
        # Base slippage
        slippage = cls.DEFAULT_SLIPPAGE
        
        # Adjust for volatility (higher vol = more slippage)
        if volatility > 0:
            vol_adjustment = min(volatility, 0.50)  # Cap at 50%
            slippage *= (1.0 + vol_adjustment)
        
        # Ensure within bounds
        min_slippage = cls.SLIPPAGE_BPS_MIN / 10000
        max_slippage = cls.SLIPPAGE_BPS_MAX / 10000
        slippage = max(min_slippage, min(slippage, max_slippage))
        
        return slippage
    
    @classmethod
    def get_annualization_factor(cls, timeframe: str) -> float:
        """
        Get annualization factor for a timeframe.
        
        Args:
            timeframe: Timeframe string (e.g., '1h', '1d')
            
        Returns:
            Annualization factor
        """
        timeframe_lower = timeframe.lower()
        
        if 'd' in timeframe_lower:
            return cls.ANNUAL_FACTOR_DAILY
        elif 'h' in timeframe_lower:
            return cls.ANNUAL_FACTOR_HOURLY
        elif 'm' in timeframe_lower:
            return cls.ANNUAL_FACTOR_MINUTELY
        else:
            return cls.ANNUAL_FACTOR_DAILY  # Default
    
    @classmethod
    def validate_leverage(cls, leverage: float) -> float:
        """
        Validate and clip leverage to acceptable range.
        
        Args:
            leverage: Requested leverage
            
        Returns:
            Valid leverage within bounds
        """
        if leverage > cls.MAX_LEVERAGE:
            from loguru import logger
            logger.warning(
                f"Leverage {leverage}x exceeds maximum {cls.MAX_LEVERAGE}x, clipping"
            )
            return cls.MAX_LEVERAGE
        
        if leverage < cls.MIN_LEVERAGE:
            return cls.MIN_LEVERAGE
        
        return leverage


# Singleton instance
constants = Constants()
