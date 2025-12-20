"""
LSTM Model for Time Series Prediction

Implements Long Short-Term Memory networks for predicting future price movements
and generating trading signals.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional
from loguru import logger


class LSTMModel(nn.Module):
    """
    LSTM-based model for time series prediction.
    
    Architecture:
        - Multiple LSTM layers with dropout
        - Fully connected output layer
        - Supports both regression and classification tasks
    
    Attributes:
        input_size: Number of input features
        hidden_size: Number of hidden units in LSTM
        num_layers: Number of LSTM layers
        output_size: Number of output units
        dropout: Dropout probability
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        """
        Initialize LSTM model.
        
        Args:
            input_size: Number of input features
            hidden_size: Number of hidden units
            num_layers: Number of LSTM layers
            output_size: Number of output units
            dropout: Dropout probability
        """
        super(LSTMModel, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        
        logger.info(
            f"Initialized LSTM model: input_size={input_size}, "
            f"hidden_size={hidden_size}, num_layers={num_layers}"
        )
    
    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass through the LSTM model.
        
        Args:
            x: Input tensor of shape (batch_size, seq_length, input_size)
            hidden: Optional hidden state tuple (h0, c0)
            
        Returns:
            Tuple of (output, hidden_state)
        """
        # LSTM forward pass
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Take the last time step output
        last_output = lstm_out[:, -1, :]
        
        # Apply dropout and fully connected layer
        out = self.dropout(last_output)
        out = self.fc(out)
        
        return out, hidden
    
    def predict(self, x: np.ndarray, device: str = "cpu") -> np.ndarray:
        """
        Make predictions on input data.
        
        Args:
            x: Input data as numpy array
            device: Device to run prediction on
            
        Returns:
            Predictions as numpy array
        """
        self.eval()
        with torch.no_grad():
            x_tensor = torch.FloatTensor(x).to(device)
            if len(x_tensor.shape) == 2:
                x_tensor = x_tensor.unsqueeze(0)
            
            output, _ = self.forward(x_tensor)
            predictions = output.cpu().numpy()
        
        return predictions
    
    def init_hidden(self, batch_size: int, device: str = "cpu") -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Initialize hidden state.
        
        Args:
            batch_size: Batch size
            device: Device for tensors
            
        Returns:
            Tuple of (h0, c0) hidden states
        """
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(device)
        return (h0, c0)


class LSTMTrainer:
    """
    Trainer class for LSTM models.
    
    Handles training loop, validation, and model checkpointing.
    """
    
    def __init__(
        self,
        model: LSTMModel,
        learning_rate: float = 0.001,
        device: str = "cpu",
    ):
        """
        Initialize trainer.
        
        Args:
            model: LSTM model to train
            learning_rate: Learning rate for optimizer
            device: Device to train on
        """
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        logger.info(f"Initialized LSTM trainer on device: {device}")
    
    def train_epoch(
        self,
        train_loader: torch.utils.data.DataLoader,
    ) -> float:
        """
        Train for one epoch.
        
        Args:
            train_loader: DataLoader for training data
            
        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0.0
        
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs, _ = self.model(batch_x)
            loss = self.criterion(outputs, batch_y)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        return avg_loss
    
    def validate(
        self,
        val_loader: torch.utils.data.DataLoader,
    ) -> float:
        """
        Validate model on validation set.
        
        Args:
            val_loader: DataLoader for validation data
            
        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                outputs, _ = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
                total_loss += loss.item()
        
        avg_loss = total_loss / len(val_loader)
        return avg_loss
