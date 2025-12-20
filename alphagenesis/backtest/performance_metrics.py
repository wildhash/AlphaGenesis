"""
Performance Metrics

Calculates comprehensive performance metrics for backtesting results.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from loguru import logger


class PerformanceMetrics:
    """
    Calculate and analyze trading strategy performance metrics.
    
    Provides various metrics including Sharpe ratio, maximum drawdown,
    win rate, profit factor, and more.
    """
    
    @staticmethod
    def calculate_returns(equity_curve: pd.Series) -> pd.Series:
        """
        Calculate returns from equity curve.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Series of returns
        """
        return equity_curve.pct_change().dropna()
    
    @staticmethod
    def sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate annualized Sharpe ratio.
        
        Args:
            returns: Returns series
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods in a year
            
        Returns:
            Sharpe ratio
        """
        if returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / periods_per_year
        sharpe = (
            excess_returns.mean() / returns.std()
        ) * np.sqrt(periods_per_year)
        
        return sharpe
    
    @staticmethod
    def sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate annualized Sortino ratio.
        
        Uses downside deviation instead of total volatility.
        
        Args:
            returns: Returns series
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods in a year
            
        Returns:
            Sortino ratio
        """
        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        sortino = (
            excess_returns.mean() / downside_returns.std()
        ) * np.sqrt(periods_per_year)
        
        return sortino
    
    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> Dict[str, Any]:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Dictionary with max drawdown, start, and end dates
        """
        cumulative_max = equity_curve.expanding().max()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        
        max_dd = drawdown.min()
        max_dd_end = drawdown.idxmin()
        max_dd_start = equity_curve[:max_dd_end].idxmax()
        
        return {
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd * 100,
            "drawdown_start": max_dd_start,
            "drawdown_end": max_dd_end,
        }
    
    @staticmethod
    def calmar_ratio(
        returns: pd.Series,
        equity_curve: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate Calmar ratio (return / max drawdown).
        
        Args:
            returns: Returns series
            equity_curve: Equity curve series
            periods_per_year: Number of periods in a year
            
        Returns:
            Calmar ratio
        """
        annual_return = returns.mean() * periods_per_year
        max_dd = abs(PerformanceMetrics.max_drawdown(equity_curve)["max_drawdown"])
        
        if max_dd == 0:
            return 0.0
        
        return annual_return / max_dd
    
    @staticmethod
    def win_rate(trades: pd.DataFrame) -> float:
        """
        Calculate win rate.
        
        Args:
            trades: DataFrame with trade information including P&L
            
        Returns:
            Win rate (percentage)
        """
        if len(trades) == 0 or "pnl" not in trades.columns:
            return 0.0
        
        winning_trades = len(trades[trades["pnl"] > 0])
        return (winning_trades / len(trades)) * 100
    
    @staticmethod
    def profit_factor(trades: pd.DataFrame) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades: DataFrame with trade information
            
        Returns:
            Profit factor
        """
        if len(trades) == 0 or "pnl" not in trades.columns:
            return 0.0
        
        gross_profit = trades[trades["pnl"] > 0]["pnl"].sum()
        gross_loss = abs(trades[trades["pnl"] < 0]["pnl"].sum())
        
        if gross_loss == 0:
            return np.inf if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.Series,
        trades: pd.DataFrame = None,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: Series of portfolio values
            trades: DataFrame with trade information
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods in a year
            
        Returns:
            Dictionary with all metrics
        """
        returns = PerformanceMetrics.calculate_returns(equity_curve)
        dd_metrics = PerformanceMetrics.max_drawdown(equity_curve)
        
        metrics = {
            "total_return": (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0],
            "total_return_pct": ((equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]) * 100,
            "annual_return": returns.mean() * periods_per_year,
            "annual_volatility": returns.std() * np.sqrt(periods_per_year),
            "sharpe_ratio": PerformanceMetrics.sharpe_ratio(
                returns, risk_free_rate, periods_per_year
            ),
            "sortino_ratio": PerformanceMetrics.sortino_ratio(
                returns, risk_free_rate, periods_per_year
            ),
            "calmar_ratio": PerformanceMetrics.calmar_ratio(
                returns, equity_curve, periods_per_year
            ),
            **dd_metrics,
        }
        
        # Add trade-specific metrics if available
        if trades is not None and len(trades) > 0:
            metrics.update({
                "total_trades": len(trades),
                "win_rate": PerformanceMetrics.win_rate(trades),
                "profit_factor": PerformanceMetrics.profit_factor(trades),
            })
        
        logger.info(f"Performance metrics calculated: Sharpe={metrics['sharpe_ratio']:.2f}")
        
        return metrics
