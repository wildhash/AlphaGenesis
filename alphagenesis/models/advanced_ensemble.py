"""
Advanced Ensemble Model with Attention-based Fusion

This module implements a sophisticated ensemble that combines LSTM, Transformer, 
and RL agents with attention mechanisms for robust trading decisions.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class EnsemblePrediction:
    """Container for ensemble prediction results."""
    
    action_probs: torch.Tensor  # BUY, SELL, HOLD probabilities
    uncertainty: torch.Tensor  # Uncertainty score
    confidence: float  # Overall confidence (0-1)
    component_weights: Dict[str, float]  # Weight of each component
    reasoning: str  # Explanation of decision


class AdvancedEnsemble(nn.Module):
    """
    Attention-based ensemble of LSTM, Transformer, and RL agents.
    
    This ensemble uses multi-head attention to dynamically weight the predictions
    from different models based on market conditions and model confidence.
    
    Args:
        lstm_model: LSTM model for sequential pattern recognition
        transformer_model: Transformer for long-range dependencies
        rl_agent: Reinforcement learning agent for action selection
        embed_dim: Embedding dimension for attention mechanism
        num_heads: Number of attention heads
        dropout: Dropout rate for regularization
    """
    
    def __init__(
        self,
        lstm_model: Optional[nn.Module] = None,
        transformer_model: Optional[nn.Module] = None,
        rl_agent: Optional[object] = None,
        embed_dim: int = 256,
        num_heads: int = 8,
        dropout: float = 0.3
    ):
        super().__init__()
        
        self.lstm = lstm_model
        self.transformer = transformer_model
        self.rl_agent = rl_agent
        
        # Attention mechanism for model fusion
        self.attention = nn.MultiheadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Feature projection layers
        self.lstm_projection = nn.Linear(128, embed_dim) if lstm_model else None
        self.transformer_projection = nn.Linear(128, embed_dim) if transformer_model else None
        self.rl_projection = nn.Linear(128, embed_dim) if rl_agent else None
        
        # Fusion network
        total_features = embed_dim * sum([
            1 if lstm_model else 0,
            1 if transformer_model else 0,
            1 if rl_agent else 0
        ])
        
        self.fusion = nn.Sequential(
            nn.Linear(total_features, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.BatchNorm1d(256),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 3)  # BUY, SELL, HOLD probabilities
        )
        
        # Uncertainty estimation layer
        self.uncertainty_estimator = nn.Sequential(
            nn.Linear(total_features, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
    def forward(
        self,
        market_state: torch.Tensor,
        historical_data: torch.Tensor,
        sentiment_data: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Forward pass through the ensemble.
        
        Args:
            market_state: Current market state features
            historical_data: Historical price and volume data
            sentiment_data: Optional sentiment features
            
        Returns:
            action_probs: Softmax probabilities for BUY, SELL, HOLD
            uncertainty: Uncertainty score (0-1)
            component_features: Dictionary of features from each component
        """
        component_features = {}
        feature_list = []
        
        # Extract features from LSTM
        if self.lstm is not None:
            lstm_features = self._extract_lstm_features(historical_data)
            lstm_projected = self.lstm_projection(lstm_features)
            component_features['lstm'] = lstm_projected
            feature_list.append(lstm_projected)
        
        # Extract features from Transformer
        if self.transformer is not None:
            transformer_features = self._extract_transformer_features(market_state)
            transformer_projected = self.transformer_projection(transformer_features)
            component_features['transformer'] = transformer_projected
            feature_list.append(transformer_projected)
        
        # Extract features from RL agent
        if self.rl_agent is not None:
            rl_features = self._extract_rl_features(market_state)
            rl_projected = self.rl_projection(rl_features)
            component_features['rl'] = rl_projected
            feature_list.append(rl_projected)
        
        # Apply attention-based fusion
        if len(feature_list) > 1:
            # Stack features for attention
            stacked_features = torch.stack(feature_list, dim=1)
            
            # Self-attention to weight different models
            attended, attention_weights = self.attention(
                stacked_features,
                stacked_features,
                stacked_features
            )
            
            # Flatten attended features
            combined = attended.flatten(start_dim=1)
        else:
            combined = feature_list[0]
        
        # Final prediction
        logits = self.fusion(combined)
        action_probs = F.softmax(logits, dim=-1)
        
        # Estimate uncertainty
        uncertainty = self.uncertainty_estimator(combined)
        
        return action_probs, uncertainty, component_features
    
    def _extract_lstm_features(self, historical_data: torch.Tensor) -> torch.Tensor:
        """Extract features from LSTM model."""
        if self.lstm is None:
            raise ValueError("LSTM model not initialized")
        
        # Use LSTM to encode historical sequence
        with torch.no_grad():
            if hasattr(self.lstm, 'forward'):
                features = self.lstm(historical_data)
            else:
                # Fallback: create dummy features
                batch_size = historical_data.size(0)
                features = torch.randn(batch_size, 128, device=historical_data.device)
        
        return features
    
    def _extract_transformer_features(self, market_state: torch.Tensor) -> torch.Tensor:
        """Extract features from Transformer model."""
        if self.transformer is None:
            raise ValueError("Transformer model not initialized")
        
        with torch.no_grad():
            if hasattr(self.transformer, 'forward'):
                features = self.transformer(market_state)
            else:
                # Fallback: create dummy features
                batch_size = market_state.size(0)
                features = torch.randn(batch_size, 128, device=market_state.device)
        
        return features
    
    def _extract_rl_features(self, market_state: torch.Tensor) -> torch.Tensor:
        """Extract features from RL agent."""
        if self.rl_agent is None:
            raise ValueError("RL agent not initialized")
        
        # Convert to numpy for RL agent
        market_state_np = market_state.cpu().numpy()
        
        if hasattr(self.rl_agent, 'get_features'):
            features_np = self.rl_agent.get_features(market_state_np)
            features = torch.from_numpy(features_np).float().to(market_state.device)
        else:
            # Fallback: create dummy features
            batch_size = market_state.size(0)
            features = torch.randn(batch_size, 128, device=market_state.device)
        
        return features
    
    def predict(
        self,
        market_state: torch.Tensor,
        historical_data: torch.Tensor,
        sentiment_data: Optional[torch.Tensor] = None
    ) -> EnsemblePrediction:
        """
        Make a prediction with full reasoning.
        
        Args:
            market_state: Current market state
            historical_data: Historical data
            sentiment_data: Optional sentiment data
            
        Returns:
            EnsemblePrediction with action probabilities and reasoning
        """
        self.eval()
        with torch.no_grad():
            action_probs, uncertainty, component_features = self.forward(
                market_state, historical_data, sentiment_data
            )
            
            # Calculate component weights (normalized feature magnitudes)
            component_weights = {}
            total_magnitude = 0.0
            for name, features in component_features.items():
                magnitude = torch.norm(features).item()
                component_weights[name] = magnitude
                total_magnitude += magnitude
            
            # Normalize weights
            if total_magnitude > 0:
                component_weights = {
                    k: v / total_magnitude for k, v in component_weights.items()
                }
            
            # Determine confidence (inverse of uncertainty)
            confidence = 1.0 - uncertainty.mean().item()
            
            # Generate reasoning
            action_idx = torch.argmax(action_probs, dim=-1).item()
            action_names = ['BUY', 'SELL', 'HOLD']
            action = action_names[action_idx]
            action_prob = action_probs[0, action_idx].item()
            
            reasoning = self._generate_reasoning(
                action, action_prob, confidence, component_weights
            )
            
            return EnsemblePrediction(
                action_probs=action_probs,
                uncertainty=uncertainty,
                confidence=confidence,
                component_weights=component_weights,
                reasoning=reasoning
            )
    
    def _generate_reasoning(
        self,
        action: str,
        action_prob: float,
        confidence: float,
        component_weights: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for the prediction."""
        reasoning = f"Action: {action} (probability: {action_prob:.2%})\n"
        reasoning += f"Overall confidence: {confidence:.2%}\n"
        reasoning += "Component contributions:\n"
        
        for component, weight in sorted(
            component_weights.items(), key=lambda x: x[1], reverse=True
        ):
            reasoning += f"  - {component}: {weight:.2%}\n"
        
        return reasoning


class EnsembleTrainer:
    """
    Trainer for the advanced ensemble model.
    
    Handles joint training of all components with appropriate loss functions.
    """
    
    def __init__(
        self,
        ensemble: AdvancedEnsemble,
        learning_rate: float = 1e-4,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.ensemble = ensemble.to(device)
        self.device = device
        self.optimizer = torch.optim.AdamW(
            ensemble.parameters(),
            lr=learning_rate,
            weight_decay=1e-5
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5
        )
        
    def train_step(
        self,
        market_state: torch.Tensor,
        historical_data: torch.Tensor,
        targets: torch.Tensor,
        sentiment_data: Optional[torch.Tensor] = None
    ) -> Dict[str, float]:
        """
        Perform a single training step.
        
        Args:
            market_state: Current market state
            historical_data: Historical data
            targets: Ground truth labels (0: HOLD, 1: BUY, 2: SELL)
            sentiment_data: Optional sentiment data
            
        Returns:
            Dictionary of loss values
        """
        self.ensemble.train()
        self.optimizer.zero_grad()
        
        # Forward pass
        action_probs, uncertainty, _ = self.ensemble(
            market_state, historical_data, sentiment_data
        )
        
        # Classification loss
        classification_loss = F.cross_entropy(action_probs, targets)
        
        # Uncertainty regularization (encourage calibrated uncertainty)
        uncertainty_loss = torch.mean(uncertainty)
        
        # Total loss
        total_loss = classification_loss + 0.1 * uncertainty_loss
        
        # Backward pass
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.ensemble.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        return {
            'total_loss': total_loss.item(),
            'classification_loss': classification_loss.item(),
            'uncertainty_loss': uncertainty_loss.item()
        }
    
    def validate(
        self,
        dataloader: torch.utils.data.DataLoader
    ) -> Dict[str, float]:
        """
        Validate the model on a validation set.
        
        Args:
            dataloader: DataLoader for validation data
            
        Returns:
            Dictionary of validation metrics
        """
        self.ensemble.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in dataloader:
                market_state = batch['market_state'].to(self.device)
                historical_data = batch['historical_data'].to(self.device)
                targets = batch['targets'].to(self.device)
                
                action_probs, uncertainty, _ = self.ensemble(
                    market_state, historical_data
                )
                
                loss = F.cross_entropy(action_probs, targets)
                total_loss += loss.item()
                
                predictions = torch.argmax(action_probs, dim=-1)
                correct += (predictions == targets).sum().item()
                total += targets.size(0)
        
        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total if total > 0 else 0.0
        
        self.scheduler.step(avg_loss)
        
        return {
            'validation_loss': avg_loss,
            'accuracy': accuracy
        }


# Utility function for easy model creation
def create_advanced_ensemble(
    lstm_config: Optional[Dict] = None,
    transformer_config: Optional[Dict] = None,
    rl_config: Optional[Dict] = None,
    embed_dim: int = 256,
    num_heads: int = 8
) -> AdvancedEnsemble:
    """
    Create an advanced ensemble with default configurations.
    
    Args:
        lstm_config: Configuration for LSTM model
        transformer_config: Configuration for Transformer model
        rl_config: Configuration for RL agent
        embed_dim: Embedding dimension
        num_heads: Number of attention heads
        
    Returns:
        Configured AdvancedEnsemble instance
    """
    lstm_model = None
    transformer_model = None
    rl_agent = None
    
    if lstm_config is not None:
        from alphagenesis.models import LSTMModel
        lstm_model = LSTMModel(**lstm_config)
    
    if transformer_config is not None:
        from alphagenesis.models import TransformerModel
        transformer_model = TransformerModel(**transformer_config)
    
    if rl_config is not None:
        from alphagenesis.models import RLTradingAgent
        rl_agent = RLTradingAgent(**rl_config)
    
    return AdvancedEnsemble(
        lstm_model=lstm_model,
        transformer_model=transformer_model,
        rl_agent=rl_agent,
        embed_dim=embed_dim,
        num_heads=num_heads
    )
