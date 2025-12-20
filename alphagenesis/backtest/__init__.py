"""
Backtesting Module

This module provides an event-driven backtesting framework for testing
trading strategies on historical data.

Components:
    - Event-driven backtesting engine
    - Performance metrics and analysis
    - Trade execution simulation
"""

from alphagenesis.backtest.backtester import Backtester
from alphagenesis.backtest.performance_metrics import PerformanceMetrics
from alphagenesis.backtest.metrics_report import MetricsReportGenerator

__all__ = [
    "Backtester",
    "PerformanceMetrics",
    "MetricsReportGenerator",
]
