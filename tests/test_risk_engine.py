"""
Tests for Risk Engine Components

Tests for position sizer, circuit breaker, and risk management functionality.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from alphagenesis.risk.position_sizer import PositionSizer
from alphagenesis.risk.circuit_breaker import CircuitBreaker
from alphagenesis.risk import RiskManager


class TestPositionSizer:
    """Tests for PositionSizer class."""
    
    def test_initialization(self):
        """Test PositionSizer initialization."""
        sizer = PositionSizer(
            max_position_size=0.2,
            target_volatility=0.15,
            max_leverage=20.0,
        )
        
        assert sizer.max_position_size == 0.2
        assert sizer.target_volatility == 0.15
        assert sizer.max_leverage == 20.0
    
    def test_kelly_size_calculation(self):
        """Test Kelly Criterion position sizing."""
        sizer = PositionSizer(kelly_fraction=0.25)
        
        # Test with profitable strategy
        size = sizer.calculate_kelly_size(
            win_rate=0.6,
            avg_win=0.02,
            avg_loss=0.01,
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_kelly_size_with_invalid_inputs(self):
        """Test Kelly sizing with invalid inputs."""
        sizer = PositionSizer()
        
        # Invalid win rate
        size = sizer.calculate_kelly_size(win_rate=1.5, avg_win=0.02, avg_loss=0.01)
        assert size == sizer.min_position_size
        
        # Negative avg_win
        size = sizer.calculate_kelly_size(win_rate=0.6, avg_win=-0.02, avg_loss=0.01)
        assert size == sizer.min_position_size
    
    def test_volatility_target_sizing(self):
        """Test volatility targeting position sizing."""
        sizer = PositionSizer(target_volatility=0.15)
        
        # Low volatility asset should get larger position
        size_low_vol = sizer.calculate_volatility_target_size(asset_volatility=0.10)
        
        # High volatility asset should get smaller position
        size_high_vol = sizer.calculate_volatility_target_size(asset_volatility=0.30)
        
        assert size_low_vol > size_high_vol
    
    def test_fixed_risk_sizing(self):
        """Test fixed risk position sizing."""
        sizer = PositionSizer()
        
        size = sizer.calculate_fixed_risk_size(
            entry_price=100.0,
            stop_loss_price=98.0,
            risk_per_trade=0.02,
            account_balance=100000.0,
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_optimal_size_calculation(self):
        """Test optimal position size calculation."""
        sizer = PositionSizer()
        
        result = sizer.calculate_optimal_size(
            signal_strength=0.8,
            asset_volatility=0.20,
            win_rate=0.6,
            avg_win=0.02,
            avg_loss=0.01,
        )
        
        assert 'final_size' in result
        assert 'leverage_required' in result
        assert result['final_size'] >= 0
        assert result['leverage_required'] <= sizer.max_leverage


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""
    
    def test_initialization(self):
        """Test CircuitBreaker initialization."""
        breaker = CircuitBreaker(
            max_daily_drawdown=0.10,
            max_total_drawdown=0.25,
            max_leverage=20.0,
        )
        
        assert breaker.max_daily_drawdown == 0.10
        assert breaker.max_total_drawdown == 0.25
        assert breaker.max_leverage == 20.0
        assert not breaker.is_tripped
    
    def test_leverage_check_within_limit(self):
        """Test leverage check when within limit."""
        breaker = CircuitBreaker(max_leverage=20.0)
        
        result = breaker.check_order(
            order_size=1.0,
            order_price=50000.0,
            current_equity=100000.0,
            current_positions={},
        )
        
        assert result['allowed']
    
    def test_leverage_check_exceeds_limit(self):
        """Test leverage check when exceeding limit."""
        breaker = CircuitBreaker(max_leverage=20.0)
        
        # Try to use 25x leverage
        result = breaker.check_order(
            order_size=25.0,
            order_price=100000.0,
            current_equity=100000.0,
            current_positions={},
        )
        
        assert not result['allowed']
        assert 'leverage' in result['reason'].lower()
    
    def test_leverage_cap_enforcement(self):
        """Test that 20x leverage cap is enforced (hackathon requirement)."""
        breaker = CircuitBreaker(max_leverage=20.0)
        
        # Try various leverage levels
        for leverage_multiplier in [1, 5, 10, 15, 20]:
            result = breaker.check_order(
                order_size=leverage_multiplier,
                order_price=100000.0,
                current_equity=100000.0,
                current_positions={},
            )
            assert result['allowed'], f"Leverage {leverage_multiplier}x should be allowed"
        
        # Try exceeding cap
        result = breaker.check_order(
            order_size=21,
            order_price=100000.0,
            current_equity=100000.0,
            current_positions={},
        )
        assert not result['allowed'], "Leverage 21x should not be allowed"
    
    def test_daily_drawdown_limit(self):
        """Test daily drawdown limit enforcement."""
        breaker = CircuitBreaker(max_daily_drawdown=0.10)
        
        # Start with 100k equity
        breaker.daily_start_equity = 100000.0
        breaker.daily_high_watermark = 100000.0
        breaker.last_reset_date = datetime.now().date()
        
        # Drop to 89k (11% drawdown - should trip)
        result = breaker.check_order(
            order_size=0.1,
            order_price=50000.0,
            current_equity=89000.0,
            current_positions={},
        )
        
        assert not result['allowed']
        assert breaker.is_tripped
    
    def test_total_drawdown_limit(self):
        """Test total drawdown limit enforcement."""
        breaker = CircuitBreaker(max_total_drawdown=0.25)
        
        # Set high watermark at 100k
        breaker.total_high_watermark = 100000.0
        
        # Drop to 74k (26% drawdown - should trip)
        result = breaker.check_order(
            order_size=0.1,
            order_price=50000.0,
            current_equity=74000.0,
            current_positions={},
        )
        
        assert not result['allowed']
        assert breaker.is_tripped
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker cooldown and reset."""
        breaker = CircuitBreaker(cooldown_period_minutes=1)
        
        # Trip the breaker
        breaker._trip_breaker("Test reason", datetime.now() - timedelta(minutes=2))
        
        assert breaker.is_tripped
        
        # Check if should reset (after cooldown)
        should_reset = breaker._should_reset_breaker(datetime.now())
        assert should_reset
        
        # Reset
        breaker._reset_breaker()
        assert not breaker.is_tripped
    
    def test_violation_logging(self):
        """Test violation logging."""
        breaker = CircuitBreaker()
        
        timestamp = datetime.now()
        breaker._log_violation("Test violation", timestamp)
        
        assert len(breaker.violation_log) == 1
        assert breaker.violation_log[0]['reason'] == "Test violation"
    
    def test_get_status(self):
        """Test getting circuit breaker status."""
        breaker = CircuitBreaker()
        
        status = breaker.get_status()
        
        assert 'is_tripped' in status
        assert 'violations_count' in status
        assert status['violations_count'] == 0


class TestRiskManager:
    """Tests for RiskManager class."""
    
    def test_initialization(self):
        """Test RiskManager initialization."""
        manager = RiskManager(
            max_position_size=0.2,
            max_leverage=20.0,
        )
        
        assert manager.max_position_size == 0.2
        assert manager.max_leverage == 20.0
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        manager = RiskManager()
        
        size = manager.calculate_position_size(
            capital=100000.0,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert size > 0
    
    def test_check_risk_limits(self):
        """Test risk limits checking."""
        manager = RiskManager(max_position_size=0.2)
        
        # Within limits
        result = manager.check_risk_limits(
            position_size=0.15,
            account_equity=100000.0,
        )
        assert result['allowed']
        
        # Exceeds limits
        result = manager.check_risk_limits(
            position_size=0.25,
            account_equity=100000.0,
        )
        assert not result['allowed']


class TestIntegration:
    """Integration tests for risk engine components."""
    
    def test_position_sizer_with_circuit_breaker(self):
        """Test position sizer working with circuit breaker."""
        sizer = PositionSizer(max_leverage=20.0)
        breaker = CircuitBreaker(max_leverage=20.0)
        
        # Calculate position size
        size_result = sizer.calculate_optimal_size(
            signal_strength=0.8,
            asset_volatility=0.20,
            account_balance=100000.0,
        )
        
        # Check with circuit breaker
        order_result = breaker.check_order(
            order_size=size_result['final_size'] * 100000.0 / 50000.0,
            order_price=50000.0,
            current_equity=100000.0,
            current_positions={},
        )
        
        assert order_result['allowed']
    
    def test_risk_cascade(self):
        """Test that risk checks cascade properly."""
        sizer = PositionSizer(max_leverage=20.0)
        breaker = CircuitBreaker(max_leverage=20.0, max_daily_drawdown=0.10)
        manager = RiskManager(max_leverage=20.0)
        
        # All three should agree on leverage limits
        assert sizer.max_leverage == breaker.max_leverage == manager.max_leverage


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
