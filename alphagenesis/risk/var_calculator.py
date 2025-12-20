"""
Value at Risk (VaR) Calculator

Implements various methods for calculating VaR and CVaR (Conditional VaR)
for risk assessment and portfolio management.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, Optional
from loguru import logger


class VaRCalculator:
    """
    Calculator for Value at Risk and Conditional Value at Risk.
    
    Implements multiple VaR calculation methods:
    - Historical VaR
    - Parametric VaR (assuming normal distribution)
    - Monte Carlo VaR
    - Conditional VaR (CVaR/Expected Shortfall)
    """
    
    @staticmethod
    def historical_var(
        returns: Union[pd.Series, np.ndarray],
        confidence_level: float = 0.95,
    ) -> float:
        """
        Calculate Historical Value at Risk.
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            VaR value (positive number representing potential loss)
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        # Remove NaN values
        returns = returns[~np.isnan(returns)]
        
        if len(returns) == 0:
            logger.warning("No valid returns data for VaR calculation")
            return 0.0
        
        # Calculate the percentile
        var = -np.percentile(returns, (1 - confidence_level) * 100)
        
        logger.debug(f"Historical VaR ({confidence_level*100}%): {var:.6f}")
        return var
    
    @staticmethod
    def parametric_var(
        returns: Union[pd.Series, np.ndarray],
        confidence_level: float = 0.95,
    ) -> float:
        """
        Calculate Parametric VaR assuming normal distribution.
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level
            
        Returns:
            VaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        returns = returns[~np.isnan(returns)]
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate mean and standard deviation
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # Calculate VaR using normal distribution
        z_score = stats.norm.ppf(1 - confidence_level)
        var = -(mu + z_score * sigma)
        
        logger.debug(f"Parametric VaR ({confidence_level*100}%): {var:.6f}")
        return var
    
    @staticmethod
    def monte_carlo_var(
        returns: Union[pd.Series, np.ndarray],
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        time_horizon: int = 1,
    ) -> float:
        """
        Calculate Monte Carlo VaR through simulation.
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level
            num_simulations: Number of Monte Carlo simulations
            time_horizon: Time horizon for VaR (in periods)
            
        Returns:
            VaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        returns = returns[~np.isnan(returns)]
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate mean and standard deviation
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # Simulate returns
        simulated_returns = np.random.normal(
            mu * time_horizon,
            sigma * np.sqrt(time_horizon),
            num_simulations,
        )
        
        # Calculate VaR
        var = -np.percentile(simulated_returns, (1 - confidence_level) * 100)
        
        logger.debug(f"Monte Carlo VaR ({confidence_level*100}%): {var:.6f}")
        return var
    
    @staticmethod
    def conditional_var(
        returns: Union[pd.Series, np.ndarray],
        confidence_level: float = 0.95,
    ) -> float:
        """
        Calculate Conditional VaR (CVaR/Expected Shortfall).
        
        CVaR is the expected loss given that the loss exceeds VaR.
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level
            
        Returns:
            CVaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        returns = returns[~np.isnan(returns)]
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate VaR threshold
        var = -np.percentile(returns, (1 - confidence_level) * 100)
        
        # Calculate CVaR as mean of losses exceeding VaR
        losses = -returns[returns < -var]
        cvar = np.mean(losses) if len(losses) > 0 else var
        
        logger.debug(f"Conditional VaR ({confidence_level*100}%): {cvar:.6f}")
        return cvar
    
    @staticmethod
    def portfolio_var(
        returns_matrix: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
        method: str = "historical",
    ) -> float:
        """
        Calculate portfolio VaR considering correlations.
        
        Args:
            returns_matrix: DataFrame with returns for each asset
            weights: Portfolio weights for each asset
            confidence_level: Confidence level
            method: VaR calculation method
            
        Returns:
            Portfolio VaR
        """
        # Calculate portfolio returns
        portfolio_returns = (returns_matrix * weights).sum(axis=1)
        
        # Calculate VaR based on method
        if method == "historical":
            var = VaRCalculator.historical_var(portfolio_returns, confidence_level)
        elif method == "parametric":
            var = VaRCalculator.parametric_var(portfolio_returns, confidence_level)
        elif method == "monte_carlo":
            var = VaRCalculator.monte_carlo_var(portfolio_returns, confidence_level)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return var
    
    @staticmethod
    def calculate_all_metrics(
        returns: Union[pd.Series, np.ndarray],
        confidence_level: float = 0.95,
    ) -> dict:
        """
        Calculate all VaR metrics.
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level
            
        Returns:
            Dictionary with all VaR metrics
        """
        metrics = {
            "historical_var": VaRCalculator.historical_var(returns, confidence_level),
            "parametric_var": VaRCalculator.parametric_var(returns, confidence_level),
            "monte_carlo_var": VaRCalculator.monte_carlo_var(returns, confidence_level),
            "conditional_var": VaRCalculator.conditional_var(returns, confidence_level),
        }
        
        return metrics
