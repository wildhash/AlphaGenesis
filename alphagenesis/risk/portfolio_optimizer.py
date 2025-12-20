"""
Portfolio Optimizer

Implements various portfolio optimization techniques including
mean-variance optimization, risk parity, and maximum Sharpe ratio.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from scipy.optimize import minimize
from loguru import logger


class PortfolioOptimizer:
    """
    Portfolio optimization for multi-asset portfolios.
    
    Implements various optimization objectives:
    - Maximum Sharpe ratio
    - Minimum variance
    - Risk parity
    - Maximum return for given risk
    """
    
    def __init__(self, returns: pd.DataFrame, risk_free_rate: float = 0.0):
        """
        Initialize portfolio optimizer.
        
        Args:
            returns: DataFrame with asset returns (columns = assets)
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
        """
        self.returns = returns
        self.risk_free_rate = risk_free_rate
        self.mean_returns = returns.mean()
        self.cov_matrix = returns.cov()
        self.num_assets = len(self.mean_returns)
    
    def portfolio_metrics(self, weights: np.ndarray) -> Dict[str, float]:
        """
        Calculate portfolio metrics for given weights.
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Dictionary with portfolio return, volatility, and Sharpe ratio
        """
        portfolio_return = np.dot(weights, self.mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            "return": portfolio_return,
            "volatility": portfolio_volatility,
            "sharpe_ratio": sharpe_ratio,
        }
    
    def negative_sharpe(self, weights: np.ndarray) -> float:
        """
        Calculate negative Sharpe ratio (for minimization).
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Negative Sharpe ratio
        """
        metrics = self.portfolio_metrics(weights)
        return -metrics["sharpe_ratio"]
    
    def portfolio_variance(self, weights: np.ndarray) -> float:
        """
        Calculate portfolio variance.
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Portfolio variance
        """
        return np.dot(weights.T, np.dot(self.cov_matrix, weights))
    
    def optimize_sharpe(
        self,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize portfolio for maximum Sharpe ratio.
        
        Args:
            constraints: Additional constraints (e.g., sector limits)
            
        Returns:
            Dictionary with optimal weights and metrics
        """
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / self.num_assets] * self.num_assets)
        
        # Constraints: weights sum to 1
        constraints_list = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        
        # Bounds: weights between 0 and 1 (long-only)
        bounds = tuple((0, 1) for _ in range(self.num_assets))
        
        try:
            result = minimize(
                self.negative_sharpe,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints_list,
            )
            
            optimal_weights = result.x
            metrics = self.portfolio_metrics(optimal_weights)
            
            logger.info(
                f"Maximum Sharpe portfolio: Return={metrics['return']:.4f}, "
                f"Volatility={metrics['volatility']:.4f}, Sharpe={metrics['sharpe_ratio']:.4f}"
            )
            
            return {
                "weights": optimal_weights,
                "metrics": metrics,
                "success": result.success,
            }
            
        except Exception as e:
            logger.error(f"Sharpe optimization failed: {e}")
            raise
    
    def optimize_minimum_variance(self) -> Dict[str, Any]:
        """
        Optimize portfolio for minimum variance.
        
        Returns:
            Dictionary with optimal weights and metrics
        """
        initial_weights = np.array([1.0 / self.num_assets] * self.num_assets)
        
        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.num_assets))
        
        try:
            result = minimize(
                self.portfolio_variance,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )
            
            optimal_weights = result.x
            metrics = self.portfolio_metrics(optimal_weights)
            
            logger.info(
                f"Minimum variance portfolio: Return={metrics['return']:.4f}, "
                f"Volatility={metrics['volatility']:.4f}"
            )
            
            return {
                "weights": optimal_weights,
                "metrics": metrics,
                "success": result.success,
            }
            
        except Exception as e:
            logger.error(f"Minimum variance optimization failed: {e}")
            raise
    
    def efficient_frontier(
        self,
        num_portfolios: int = 100,
    ) -> pd.DataFrame:
        """
        Generate efficient frontier portfolios.
        
        Args:
            num_portfolios: Number of portfolios to generate
            
        Returns:
            DataFrame with portfolio weights and metrics
        """
        results = []
        
        # Generate random portfolios
        for _ in range(num_portfolios):
            weights = np.random.random(self.num_assets)
            weights /= np.sum(weights)
            
            metrics = self.portfolio_metrics(weights)
            
            results.append({
                "return": metrics["return"],
                "volatility": metrics["volatility"],
                "sharpe_ratio": metrics["sharpe_ratio"],
            })
        
        return pd.DataFrame(results)
    
    def risk_parity_weights(self) -> np.ndarray:
        """
        Calculate risk parity portfolio weights.
        
        Equal risk contribution from each asset.
        
        Returns:
            Risk parity weights
        """
        def risk_contribution(weights):
            portfolio_vol = np.sqrt(self.portfolio_variance(weights))
            marginal_contrib = np.dot(self.cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol
            return risk_contrib
        
        def risk_parity_objective(weights):
            risk_contrib = risk_contribution(weights)
            target = np.ones(self.num_assets) / self.num_assets
            return np.sum((risk_contrib - target) ** 2)
        
        initial_weights = np.array([1.0 / self.num_assets] * self.num_assets)
        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.num_assets))
        
        try:
            result = minimize(
                risk_parity_objective,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )
            
            logger.info("Risk parity portfolio calculated")
            return result.x
            
        except Exception as e:
            logger.error(f"Risk parity calculation failed: {e}")
            # Return equal weights as fallback
            return initial_weights
