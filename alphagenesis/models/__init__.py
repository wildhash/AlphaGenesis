"""
Machine Learning Models Module

This module contains various ML models for price prediction and trading signal generation,
including deep learning models (LSTM, Transformers) and reinforcement learning agents.

Components:
    - LSTM models for time series prediction
    - Transformer models for sequence modeling
    - Reinforcement learning agents for trading strategies
    - Model training and evaluation utilities
"""

import logging
logger = logging.getLogger(__name__)


try:
    from alphagenesis.models.lstm_model import LSTMModel
except ModuleNotFoundError as e:
    LSTMModel = None
    logger.warning("LSTM disabled: %s", e)
from alphagenesis.models.transformer_model import TransformerModel
from alphagenesis.models.rl_agent import RLTradingAgent
from alphagenesis.models.ensemble import EnsemblePredictor
from alphagenesis.models.train_pipeline import TrainingPipeline

__all__ = [
    "LSTMModel",
    "TransformerModel",
    "RLTradingAgent",
    "EnsemblePredictor",
    "TrainingPipeline",
]
