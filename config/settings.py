"""
Settings Module

Centralized configuration for API keys, risk limits, and trading parameters.
Uses environment variables for sensitive data.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field
from loguru import logger


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Critical settings:
    - WEEX API credentials
    - Risk limits (leverage cap: 20x)
    - Trading pairs
    - Model parameters
    """
    
    # WEEX API Configuration
    weex_api_key: str = Field(default="", env="WEEX_API_KEY")
    weex_api_secret: str = Field(default="", env="WEEX_API_SECRET")
    weex_api_passphrase: str = Field(default="", env="WEEX_API_PASSPHRASE")
    weex_base_url: str = Field(
        default="https://api.weex.com",
        env="WEEX_BASE_URL"
    )
    weex_testnet: bool = Field(default=False, env="WEEX_TESTNET")
    
    # Risk Management Settings
    max_leverage: float = Field(
        default=20.0,
        description="Maximum leverage (WEEX hackathon cap: 20x)"
    )
    max_position_size: float = Field(
        default=0.3,
        description="Maximum single position size as fraction of portfolio"
    )
    max_daily_drawdown: float = Field(
        default=0.10,
        description="Maximum daily drawdown (10%)"
    )
    max_total_drawdown: float = Field(
        default=0.25,
        description="Maximum total drawdown (25%)"
    )
    stop_loss_pct: float = Field(
        default=0.02,
        description="Default stop loss percentage"
    )
    take_profit_pct: float = Field(
        default=0.04,
        description="Default take profit percentage"
    )
    
    # Trading Configuration
    trading_pairs: List[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        description="Trading pairs to trade"
    )
    default_timeframe: str = Field(
        default="1h",
        description="Default candlestick timeframe"
    )
    initial_capital: float = Field(
        default=100000.0,
        description="Initial capital for trading"
    )
    
    # Model Configuration
    model_device: str = Field(
        default="cuda",
        env="MODEL_DEVICE",
        description="Device for model training (cuda/cpu)"
    )
    model_checkpoint_dir: str = Field(
        default="./models/saved",
        description="Directory for saved model checkpoints"
    )
    
    # Data Configuration
    data_dir: str = Field(
        default="./data",
        description="Directory for storing market data"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable data caching"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        default="alphagenesis.log",
        description="Log file path"
    )
    
    # Backtesting Configuration
    backtest_start_date: Optional[str] = Field(
        default=None,
        description="Backtest start date (YYYY-MM-DD)"
    )
    backtest_end_date: Optional[str] = Field(
        default=None,
        description="Backtest end date (YYYY-MM-DD)"
    )
    
    # Performance Configuration
    enable_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )
    prometheus_port: int = Field(
        default=9090,
        description="Prometheus metrics port"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def validate_api_credentials(self) -> bool:
        """
        Validate that required API credentials are set.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.weex_api_key or not self.weex_api_secret:
            logger.error("WEEX API credentials not configured")
            return False
        
        logger.info("WEEX API credentials configured")
        return True
    
    def validate_risk_limits(self) -> bool:
        """
        Validate that risk limits are within acceptable ranges.
        
        Returns:
            True if limits are valid, False otherwise
        """
        issues = []
        
        # Check leverage cap (CRITICAL for hackathon)
        if self.max_leverage > 20.0:
            issues.append(
                f"⚠️  LEVERAGE CAP VIOLATION: max_leverage={self.max_leverage}x "
                f"exceeds hackathon limit of 20x"
            )
        
        # Check drawdown limits
        if self.max_daily_drawdown > 0.20:
            issues.append(
                f"Daily drawdown limit too high: {self.max_daily_drawdown:.1%}"
            )
        
        if self.max_total_drawdown > 0.50:
            issues.append(
                f"Total drawdown limit too high: {self.max_total_drawdown:.1%}"
            )
        
        # Check position size
        if self.max_position_size > 0.5:
            issues.append(
                f"Max position size too high: {self.max_position_size:.1%}"
            )
        
        if issues:
            for issue in issues:
                logger.error(issue)
            return False
        
        logger.info("Risk limits validated successfully")
        logger.info(f"  Max Leverage: {self.max_leverage}x (Hackathon Cap: 20x)")
        logger.info(f"  Max Daily DD: {self.max_daily_drawdown:.1%}")
        logger.info(f"  Max Total DD: {self.max_total_drawdown:.1%}")
        logger.info(f"  Max Position: {self.max_position_size:.1%}")
        
        return True
    
    def get_trading_pair_configs(self) -> dict:
        """
        Get trading pair specific configurations.
        
        Returns:
            Dictionary of trading pair configs
        """
        # Default config for all pairs
        default_config = {
            'min_order_size': 0.001,
            'tick_size': 0.01,
            'commission_rate': 0.001,
            'slippage_rate': 0.0005,
        }
        
        # Pair-specific overrides
        pair_configs = {}
        for pair in self.trading_pairs:
            pair_configs[pair] = default_config.copy()
        
        return pair_configs


# Global settings instance
settings = Settings()

# Validate on import
if not settings.validate_api_credentials():
    logger.warning(
        "API credentials not configured. Set WEEX_API_KEY and WEEX_API_SECRET "
        "environment variables."
    )

if not settings.validate_risk_limits():
    logger.error("Risk limits validation failed. Please review configuration.")
