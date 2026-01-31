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

# Optional imports - gracefully handle missing dependencies
__all__ = []

try:
    from alphagenesis.models.lstm_model import LSTMModel
    __all__.append("LSTMModel")
except ImportError as e:
    logger.warning(f"LSTM model unavailable (missing torch): {e}")
    LSTMModel = None

try:
    from alphagenesis.models.transformer_model import TransformerModel
    __all__.append("TransformerModel")
except ImportError as e:
    logger.warning(f"Transformer model unavailable: {e}")
    TransformerModel = None

try:
    from alphagenesis.models.rl_agent import RLTradingAgent
    __all__.append("RLTradingAgent")
except ImportError as e:
    logger.warning(f"RL agent unavailable: {e}")
    RLTradingAgent = None

try:
    from alphagenesis.models.ensemble import EnsemblePredictor
    __all__.append("EnsemblePredictor")
except ImportError as e:
    logger.warning(f"Ensemble predictor unavailable: {e}")
    EnsemblePredictor = None

try:
    from alphagenesis.models.train_pipeline import TrainingPipeline
    __all__.append("TrainingPipeline")
except ImportError as e:
    logger.warning(f"Training pipeline unavailable: {e}")
    TrainingPipeline = None
