"""
Transformer Model for Time Series Prediction

Implements Transformer-based architecture for financial time series forecasting.
"""

import torch
import torch.nn as nn
import math
from typing import Optional
from loguru import logger


class PositionalEncoding(nn.Module):
    """
    Positional encoding for transformer models.
    
    Adds position information to the input embeddings.
    """
    
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        """
        Initialize positional encoding.
        
        Args:
            d_model: Embedding dimension
            max_len: Maximum sequence length
            dropout: Dropout probability
        """
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding matrix
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer("pe", pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding to input.
        
        Args:
            x: Input tensor of shape (seq_length, batch_size, d_model)
            
        Returns:
            Tensor with positional encoding added
        """
        x = x + self.pe[: x.size(0)]
        return self.dropout(x)


class TransformerModel(nn.Module):
    """
    Transformer-based model for time series prediction.
    
    Uses multi-head self-attention to capture long-range dependencies
    in financial time series data.
    
    Attributes:
        input_size: Number of input features
        d_model: Model dimension
        nhead: Number of attention heads
        num_layers: Number of transformer layers
        dim_feedforward: Dimension of feedforward network
        output_size: Number of output units
        dropout: Dropout probability
    """
    
    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 3,
        dim_feedforward: int = 512,
        output_size: int = 1,
        dropout: float = 0.1,
    ):
        """
        Initialize Transformer model.
        
        Args:
            input_size: Number of input features
            d_model: Model dimension (must be divisible by nhead)
            nhead: Number of attention heads
            num_layers: Number of transformer layers
            dim_feedforward: Dimension of feedforward network
            output_size: Number of output units
            dropout: Dropout probability
        """
        super(TransformerModel, self).__init__()
        
        self.input_size = input_size
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        
        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output projection
        self.decoder = nn.Linear(d_model, output_size)
        
        logger.info(
            f"Initialized Transformer model: d_model={d_model}, "
            f"nhead={nhead}, num_layers={num_layers}"
        )
    
    def forward(self, src: torch.Tensor, src_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the Transformer model.
        
        Args:
            src: Input tensor of shape (batch_size, seq_length, input_size)
            src_mask: Optional source mask
            
        Returns:
            Output tensor
        """
        # Project input to d_model dimensions
        src = self.input_projection(src) * math.sqrt(self.d_model)
        
        # Add positional encoding (need to transpose for pos_encoder)
        src = src.transpose(0, 1)  # (seq_length, batch_size, d_model)
        src = self.pos_encoder(src)
        src = src.transpose(0, 1)  # (batch_size, seq_length, d_model)
        
        # Transformer encoding
        output = self.transformer_encoder(src, src_mask)
        
        # Take the last time step output
        output = output[:, -1, :]
        
        # Decode to output size
        output = self.decoder(output)
        
        return output
    
    def generate_square_subsequent_mask(self, sz: int) -> torch.Tensor:
        """
        Generate a square mask for the sequence.
        
        Args:
            sz: Size of the mask
            
        Returns:
            Mask tensor
        """
        mask = torch.triu(torch.ones(sz, sz), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        return mask
    
    def predict(self, x: torch.Tensor, device: str = "cpu") -> torch.Tensor:
        """
        Make predictions on input data.
        
        Args:
            x: Input data as tensor
            device: Device to run prediction on
            
        Returns:
            Predictions as tensor
        """
        self.eval()
        with torch.no_grad():
            x = x.to(device)
            if len(x.shape) == 2:
                x = x.unsqueeze(0)
            
            output = self.forward(x)
        
        return output


class TransformerTrainer:
    """
    Trainer class for Transformer models.
    
    Handles training loop, validation, and model checkpointing.
    """
    
    def __init__(
        self,
        model: TransformerModel,
        learning_rate: float = 0.0001,
        device: str = "cpu",
    ):
        """
        Initialize trainer.
        
        Args:
            model: Transformer model to train
            learning_rate: Learning rate for optimizer
            device: Device to train on
        """
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        logger.info(f"Initialized Transformer trainer on device: {device}")
    
    def train_epoch(self, train_loader: torch.utils.data.DataLoader) -> float:
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
            outputs = self.model(batch_x)
            loss = self.criterion(outputs, batch_y)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
            self.optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        return avg_loss
    
    def validate(self, val_loader: torch.utils.data.DataLoader) -> float:
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
                
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
                total_loss += loss.item()
        
        avg_loss = total_loss / len(val_loader)
        return avg_loss
