"""
Position Sizing Module

Implements sophisticated position sizing algorithms based on Kelly Criterion,
volatility targeting, and risk-adjusted returns.
"""

from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
from loguru import logger


class PositionSizer:
    """
    Advanced position sizing using Kelly Criterion and volatility-based methods.
    
    Determines optimal position size based on:
    - Win rate and profit factor (Kelly Criterion)
    - Account volatility targeting
    - Maximum risk per trade
    - Current market volatility
    """
    
    def __init__(
        self,
        max_position_size: float = 0.30,  # INCREASED: 30% for competition (was 10%)
        target_volatility: float = 0.15,
        max_leverage: float = 20.0,
        kelly_fraction: float = 0.50,  # INCREASED: 50% for competition (was 25%)
        min_position_size: float = 0.05,  # INCREASED: 5% minimum (was 1%)
    ):
        """
        Initialize PositionSizer - COMPETITION SETTINGS.

        Args:
            max_position_size: Maximum position size as fraction of portfolio (0-1)
            target_volatility: Target annual volatility for the portfolio
            max_leverage: Maximum allowed leverage (hackathon cap: 20x)
            kelly_fraction: Fraction of Kelly to use (aggressive: 0.5 for competition)
            min_position_size: Minimum position size as fraction of portfolio
        """
        self.max_position_size = max_position_size
        self.target_volatility = target_volatility
        self.max_leverage = max_leverage
        self.kelly_fraction = kelly_fraction
        self.min_position_size = min_position_size
        
        logger.info(
            f"PositionSizer initialized: max_pos={max_position_size}, "
            f"target_vol={target_volatility}, max_lev={max_leverage}, "
            f"kelly_frac={kelly_fraction}"
        )
    
    def calculate_kelly_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Kelly Formula: f* = (p*b - q) / b
        where:
            p = win rate
            q = loss rate = 1 - p
            b = avg_win / avg_loss
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive number)
            
        Returns:
            Recommended position size as fraction of portfolio
        """
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"Invalid win_rate: {win_rate}, returning min size")
            return self.min_position_size
        
        if avg_win <= 0 or avg_loss <= 0:
            logger.warning(f"Invalid avg_win/loss: {avg_win}/{avg_loss}, returning min size")
            return self.min_position_size
        
        # Kelly formula
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss
        
        kelly_size = (p * b - q) / b
        
        # Apply conservative fraction
        fractional_kelly = kelly_size * self.kelly_fraction
        
        # Ensure within bounds
        position_size = np.clip(
            fractional_kelly,
            self.min_position_size,
            self.max_position_size
        )
        
        logger.debug(
            f"Kelly sizing: win_rate={win_rate:.3f}, b={b:.3f}, "
            f"kelly={kelly_size:.3f}, fractional={position_size:.3f}"
        )
        
        return position_size
    
    def calculate_volatility_target_size(
        self,
        asset_volatility: float,
        current_leverage: float = 1.0,
    ) -> float:
        """
        Calculate position size to achieve target portfolio volatility.
        
        Position_size = target_vol / (asset_vol * current_leverage)
        
        Args:
            asset_volatility: Annualized volatility of the asset
            current_leverage: Current leverage being used
            
        Returns:
            Recommended position size as fraction of portfolio
        """
        if asset_volatility <= 0:
            logger.warning(f"Invalid asset_volatility: {asset_volatility}")
            return self.min_position_size
        
        # Calculate size to achieve target volatility
        position_size = self.target_volatility / (asset_volatility * current_leverage)
        
        # Ensure within bounds
        position_size = np.clip(
            position_size,
            self.min_position_size,
            self.max_position_size
        )
        
        logger.debug(
            f"Vol target sizing: asset_vol={asset_volatility:.3f}, "
            f"target_vol={self.target_volatility:.3f}, size={position_size:.3f}"
        )
        
        return position_size
    
    def calculate_fixed_risk_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = 0.02,
        account_balance: float = 100000.0,
    ) -> float:
        """
        Calculate position size based on fixed risk per trade.
        
        Position_size = (account_balance * risk_per_trade) / (entry_price - stop_loss)
        
        Args:
            entry_price: Intended entry price
            stop_loss_price: Stop loss price
            risk_per_trade: Maximum risk per trade as fraction of account
            account_balance: Current account balance
            
        Returns:
            Position size in base currency units
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            logger.warning("Invalid entry or stop loss price")
            return 0.0
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            logger.warning("Risk per unit is zero (entry == stop)")
            return 0.0
        
        # Calculate position size
        risk_amount = account_balance * risk_per_trade
        position_size = risk_amount / risk_per_unit
        
        # Convert to fraction of account
        position_fraction = (position_size * entry_price) / account_balance
        
        # Ensure within bounds
        position_fraction = np.clip(
            position_fraction,
            self.min_position_size,
            self.max_position_size
        )
        
        logger.debug(
            f"Fixed risk sizing: risk_per_trade={risk_per_trade:.3f}, "
            f"risk_per_unit={risk_per_unit:.2f}, position_frac={position_fraction:.3f}"
        )
        
        return position_fraction
    
    def calculate_optimal_size(
        self,
        signal_strength: float,
        asset_volatility: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        account_balance: float = 100000.0,
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size using multiple methods and combine them.
        
        Args:
            signal_strength: Trading signal strength (-1 to 1)
            asset_volatility: Asset's annualized volatility
            win_rate: Historical win rate (optional)
            avg_win: Average winning trade (optional)
            avg_loss: Average losing trade (optional)
            account_balance: Current account balance
            
        Returns:
            Dictionary with position sizing recommendations
        """
        results = {
            'signal_strength': signal_strength,
            'asset_volatility': asset_volatility,
        }
        
        # Volatility-based sizing (always available)
        vol_size = self.calculate_volatility_target_size(asset_volatility)
        results['vol_target_size'] = vol_size
        
        # Kelly sizing (if statistics available)
        if win_rate is not None and avg_win is not None and avg_loss is not None:
            kelly_size = self.calculate_kelly_size(win_rate, avg_win, avg_loss)
            results['kelly_size'] = kelly_size
            
            # Combined size (average of kelly and vol)
            combined_size = (kelly_size + vol_size) / 2.0
        else:
            combined_size = vol_size
        
        # Scale by signal strength
        scaled_size = combined_size * abs(signal_strength)
        
        # Apply final bounds
        final_size = np.clip(
            scaled_size,
            self.min_position_size if abs(signal_strength) > 0.1 else 0.0,
            self.max_position_size
        )
        
        # Calculate leverage required
        leverage_required = final_size / (account_balance / account_balance)  # Simplified
        if leverage_required > self.max_leverage:
            logger.warning(
                f"Leverage {leverage_required:.2f}x exceeds max {self.max_leverage}x, "
                f"reducing position size"
            )
            final_size = self.max_leverage * (account_balance / account_balance)
            leverage_required = self.max_leverage
        
        results.update({
            'combined_size': combined_size,
            'scaled_size': scaled_size,
            'final_size': final_size,
            'leverage_required': leverage_required,
            'direction': 'long' if signal_strength > 0 else 'short',
        })
        
        logger.info(
            f"Optimal size calculation: signal={signal_strength:.3f}, "
            f"vol_size={vol_size:.3f}, final_size={final_size:.3f}, "
            f"leverage={leverage_required:.2f}x"
        )
        
        return results
    
    def calculate_pyramid_sizes(
        self,
        base_size: float,
        n_entries: int = 3,
        scaling_factor: float = 0.5,
    ) -> list[float]:
        """
        Calculate position sizes for pyramiding into a position.
        
        Each additional entry is smaller than the previous one.
        
        Args:
            base_size: Initial position size
            n_entries: Number of entry points
            scaling_factor: How much to scale down each entry (0-1)
            
        Returns:
            List of position sizes for each entry
        """
        sizes = []
        current_size = base_size
        
        for i in range(n_entries):
            sizes.append(current_size)
            current_size *= scaling_factor
        
        # Normalize so total doesn't exceed max_position_size
        total_size = sum(sizes)
        if total_size > self.max_position_size:
            scaling = self.max_position_size / total_size
            sizes = [s * scaling for s in sizes]
        
        logger.debug(f"Pyramid sizes for {n_entries} entries: {sizes}")
        
        return sizes
    
    def adjust_size_for_correlation(
        self,
        base_size: float,
        correlation_matrix: pd.DataFrame,
        current_positions: Dict[str, float],
        new_symbol: str,
    ) -> float:
        """
        Adjust position size based on correlation with existing positions.
        
        Reduces size if highly correlated with existing positions to avoid
        concentration risk.
        
        Args:
            base_size: Initial calculated position size
            correlation_matrix: Asset correlation matrix
            current_positions: Dictionary of symbol -> position_size
            new_symbol: Symbol for new position
            
        Returns:
            Adjusted position size
        """
        if not current_positions or new_symbol not in correlation_matrix.index:
            return base_size
        
        # Calculate weighted average correlation
        correlations = []
        weights = []
        
        for symbol, pos_size in current_positions.items():
            if symbol in correlation_matrix.columns and symbol != new_symbol:
                corr = correlation_matrix.loc[new_symbol, symbol]
                correlations.append(abs(corr))  # Use absolute correlation
                weights.append(abs(pos_size))
        
        if not correlations:
            return base_size
        
        avg_correlation = np.average(correlations, weights=weights)
        
        # Reduce size if highly correlated
        # If avg correlation is 0.8+, reduce size by up to 50%
        if avg_correlation > 0.5:
            reduction_factor = 1.0 - (avg_correlation - 0.5) * 0.5
            adjusted_size = base_size * reduction_factor
            
            logger.info(
                f"Adjusted size for correlation: avg_corr={avg_correlation:.3f}, "
                f"reduction_factor={reduction_factor:.3f}, "
                f"adjusted_size={adjusted_size:.3f}"
            )
            
            return adjusted_size
        
        return base_size
