"""
Risk Manager

Central risk management system that coordinates various risk controls,
position sizing, and portfolio-level risk monitoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from loguru import logger

from alphagenesis.risk.var_calculator import VaRCalculator
from alphagenesis.risk.garch_model import GARCHModel


class RiskManager:
    """
    Central risk management system for the trading platform.
    
    Manages risk limits, position sizing, and portfolio-level risk controls.
    
    Attributes:
        max_position_size: Maximum position size as fraction of portfolio
        max_leverage: Maximum allowed leverage
        stop_loss_pct: Stop loss percentage
        var_limit: VaR limit as fraction of portfolio
    """
    
    def __init__(
        self,
        max_position_size: float = 0.1,
        max_leverage: float = 3.0,
        stop_loss_pct: float = 0.02,
        var_limit: float = 0.05,
    ):
        """
        Initialize risk manager.
        
        Args:
            max_position_size: Maximum position size (0-1)
            max_leverage: Maximum leverage ratio
            stop_loss_pct: Stop loss percentage
            var_limit: Maximum VaR as fraction of portfolio
        """
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.stop_loss_pct = stop_loss_pct
        self.var_limit = var_limit
        
        self.var_calculator = VaRCalculator()
        
        logger.info(
            f"Risk Manager initialized: max_position={max_position_size}, "
            f"max_leverage={max_leverage}, stop_loss={stop_loss_pct}"
        )
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price
            risk_per_trade: Maximum risk per trade as fraction of portfolio
            
        Returns:
            Position size (number of units)
        """
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            logger.warning("Risk per unit is zero, using default position size")
            return portfolio_value * self.max_position_size / entry_price
        
        # Calculate position size based on risk
        risk_amount = portfolio_value * risk_per_trade
        position_size = risk_amount / risk_per_unit
        
        # Apply maximum position size constraint
        max_units = (portfolio_value * self.max_position_size) / entry_price
        position_size = min(position_size, max_units)
        
        logger.debug(
            f"Position size: {position_size:.4f} units "
            f"(risk: {risk_per_trade*100:.2f}% of portfolio)"
        )
        
        return position_size
    
    def check_risk_limits(
        self,
        position_value: float,
        portfolio_value: float,
        current_leverage: float,
    ) -> Dict[str, bool]:
        """
        Check if position meets risk limits.
        
        Args:
            position_value: Value of the position
            portfolio_value: Current portfolio value
            current_leverage: Current leverage ratio
            
        Returns:
            Dictionary with limit check results
        """
        checks = {
            "position_size_ok": (position_value / portfolio_value) <= self.max_position_size,
            "leverage_ok": current_leverage <= self.max_leverage,
        }
        
        all_passed = all(checks.values())
        checks["all_passed"] = all_passed
        
        if not all_passed:
            logger.warning(f"Risk limit violations: {checks}")
        
        return checks
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        atr: Optional[float] = None,
        atr_multiplier: float = 2.0,
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: Position side ('long' or 'short')
            atr: Average True Range (for ATR-based stops)
            atr_multiplier: Multiplier for ATR-based stops
            
        Returns:
            Stop loss price
        """
        if atr is not None:
            # ATR-based stop loss
            stop_distance = atr * atr_multiplier
        else:
            # Percentage-based stop loss
            stop_distance = entry_price * self.stop_loss_pct
        
        if side.lower() == "long":
            stop_loss = entry_price - stop_distance
        else:  # short
            stop_loss = entry_price + stop_distance
        
        logger.debug(f"Stop loss for {side} position at {entry_price}: {stop_loss:.2f}")
        return stop_loss
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss_price: float,
        side: str,
        risk_reward_ratio: float = 2.0,
    ) -> float:
        """
        Calculate take profit price based on risk-reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            side: Position side ('long' or 'short')
            risk_reward_ratio: Target risk-reward ratio
            
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss_price)
        reward = risk * risk_reward_ratio
        
        if side.lower() == "long":
            take_profit = entry_price + reward
        else:  # short
            take_profit = entry_price - reward
        
        logger.debug(
            f"Take profit for {side} position: {take_profit:.2f} "
            f"(R:R = 1:{risk_reward_ratio})"
        )
        return take_profit
    
    def assess_portfolio_risk(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Assess overall portfolio risk.
        
        Args:
            returns: Portfolio returns
            confidence_level: Confidence level for VaR
            
        Returns:
            Dictionary with risk metrics
        """
        var_metrics = self.var_calculator.calculate_all_metrics(
            returns,
            confidence_level,
        )
        
        # Check if VaR exceeds limit
        historical_var = var_metrics["historical_var"]
        var_exceeded = historical_var > self.var_limit
        
        risk_assessment = {
            **var_metrics,
            "var_limit": self.var_limit,
            "var_exceeded": var_exceeded,
            "return_mean": returns.mean(),
            "return_std": returns.std(),
            "sharpe_ratio": returns.mean() / returns.std() if returns.std() > 0 else 0,
        }
        
        if var_exceeded:
            logger.warning(
                f"Portfolio VaR ({historical_var:.4f}) exceeds limit ({self.var_limit:.4f})"
            )
        
        return risk_assessment
    
    def suggest_portfolio_adjustment(
        self,
        current_weights: np.ndarray,
        risk_assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest portfolio adjustments based on risk assessment.
        
        Args:
            current_weights: Current portfolio weights
            risk_assessment: Risk assessment results
            
        Returns:
            Dictionary with adjustment suggestions
        """
        suggestions = {
            "reduce_positions": risk_assessment["var_exceeded"],
            "current_var": risk_assessment["historical_var"],
            "target_var": self.var_limit,
        }
        
        if risk_assessment["var_exceeded"]:
            # Suggest scaling down positions
            scale_factor = self.var_limit / risk_assessment["historical_var"]
            suggested_weights = current_weights * scale_factor
            suggestions["suggested_weights"] = suggested_weights
            suggestions["action"] = "Reduce position sizes to manage risk"
        else:
            suggestions["suggested_weights"] = current_weights
            suggestions["action"] = "Portfolio risk within acceptable limits"
        
        return suggestions
