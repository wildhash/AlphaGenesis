"""
Circuit Breaker Module

Enforces hard stops for maximum drawdown limits and leverage caps.
Critical for risk management and hackathon compliance.
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger


class CircuitBreaker:
    """
    Circuit breaker for risk management and compliance.
    
    Enforces:
    - Maximum daily drawdown (10%)
    - Maximum total drawdown (25%)
    - Maximum leverage cap (20x per hackathon rules)
    - Position size limits
    - Loss limits per time period
    
    Logs all violations for audit trail.
    """
    
    def __init__(
        self,
        max_daily_drawdown: float = 0.10,
        max_total_drawdown: float = 0.25,
        max_leverage: float = 20.0,
        max_position_size: float = 0.3,
        max_hourly_loss: float = 0.05,
        cooldown_period_minutes: int = 60,
    ):
        """
        Initialize CircuitBreaker.
        
        Args:
            max_daily_drawdown: Maximum daily drawdown allowed (0-1)
            max_total_drawdown: Maximum total drawdown allowed (0-1)
            max_leverage: Maximum leverage allowed (hackathon: 20x)
            max_position_size: Maximum single position size (0-1)
            max_hourly_loss: Maximum loss per hour (0-1)
            cooldown_period_minutes: Minutes to wait after breaker trips
        """
        self.max_daily_drawdown = max_daily_drawdown
        self.max_total_drawdown = max_total_drawdown
        self.max_leverage = max_leverage
        self.max_position_size = max_position_size
        self.max_hourly_loss = max_hourly_loss
        self.cooldown_period_minutes = cooldown_period_minutes
        
        # State tracking
        self.is_tripped = False
        self.trip_reason = None
        self.trip_time = None
        self.violation_log = []
        
        # Performance tracking
        self.daily_high_watermark = None
        self.total_high_watermark = None
        self.daily_start_equity = None
        self.last_reset_date = None
        self.hourly_start_equity = None
        self.last_hourly_reset = None
        
        logger.info(
            f"CircuitBreaker initialized: "
            f"max_daily_dd={max_daily_drawdown:.1%}, "
            f"max_total_dd={max_total_drawdown:.1%}, "
            f"max_leverage={max_leverage}x, "
            f"max_position={max_position_size:.1%}"
        )
        
        # Log leverage cap enforcement for hackathon compliance
        logger.warning(
            f"⚠️  LEVERAGE CAP ENFORCEMENT ACTIVE: {max_leverage}x "
            f"(WEEX AI Wars Hackathon Requirement)"
        )
    
    def check_order(
        self,
        order_size: float,
        order_price: float,
        current_equity: float,
        current_positions: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Check if an order is allowed under current risk constraints.
        
        Args:
            order_size: Size of the order (in base currency)
            order_price: Price of the order
            current_equity: Current account equity
            current_positions: Dictionary of current positions
            timestamp: Current timestamp
            
        Returns:
            Dictionary with 'allowed' (bool), 'reason' (str), and 'modified_size' (float)
        """
        timestamp = timestamp or datetime.now()
        
        result = {
            'allowed': True,
            'reason': None,
            'modified_size': order_size,
            'timestamp': timestamp,
        }
        
        # Check if circuit breaker is tripped
        if self.is_tripped:
            if self._should_reset_breaker(timestamp):
                self._reset_breaker()
                logger.info("Circuit breaker reset after cooldown period")
            else:
                result['allowed'] = False
                result['reason'] = f"Circuit breaker tripped: {self.trip_reason}"
                logger.warning(f"Order rejected: {result['reason']}")
                return result
        
        # Check leverage limit (CRITICAL FOR HACKATHON)
        leverage_check = self._check_leverage(
            order_size, order_price, current_equity, current_positions
        )
        if not leverage_check['allowed']:
            self._log_violation(leverage_check['reason'], timestamp, order_details={
                'order_size': order_size,
                'order_price': order_price,
                'calculated_leverage': leverage_check.get('calculated_leverage'),
            })
            return leverage_check
        
        # Check position size limit
        position_check = self._check_position_size(order_size, order_price, current_equity)
        if not position_check['allowed']:
            self._log_violation(position_check['reason'], timestamp)
            return position_check
        
        # Check drawdown limits
        drawdown_check = self._check_drawdowns(current_equity, timestamp)
        if not drawdown_check['allowed']:
            self._trip_breaker(drawdown_check['reason'], timestamp)
            return drawdown_check
        
        logger.debug(f"Order check passed: size={order_size}, price={order_price}")
        return result
    
    def _check_leverage(
        self,
        order_size: float,
        order_price: float,
        current_equity: float,
        current_positions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check if order would exceed leverage limit.
        
        CRITICAL: Enforces 20x leverage cap per WEEX hackathon rules.
        """
        # Calculate total position value including new order
        order_value = abs(order_size * order_price)
        
        # Calculate existing position value
        existing_value = 0.0
        for symbol, position in current_positions.items():
            if isinstance(position, dict):
                existing_value += abs(position.get('size', 0) * position.get('price', 0))
            else:
                # Handle simple position size
                existing_value += abs(position * order_price)
        
        total_position_value = existing_value + order_value
        
        # Calculate leverage
        if current_equity > 0:
            leverage = total_position_value / current_equity
        else:
            leverage = float('inf')
        
        # Check against limit
        if leverage > self.max_leverage:
            logger.error(
                f"🚨 LEVERAGE VIOLATION: Calculated leverage {leverage:.2f}x "
                f"exceeds maximum {self.max_leverage}x (HACKATHON RULE)"
            )
            
            # Calculate maximum allowed order size
            max_total_value = current_equity * self.max_leverage
            max_order_value = max_total_value - existing_value
            max_order_size = max_order_value / order_price if order_price > 0 else 0
            
            return {
                'allowed': False,
                'reason': f"Leverage limit exceeded: {leverage:.2f}x > {self.max_leverage}x",
                'calculated_leverage': leverage,
                'max_allowed_size': max_order_size,
                'modified_size': 0,
            }
        
        return {'allowed': True, 'calculated_leverage': leverage}
    
    def _check_position_size(
        self,
        order_size: float,
        order_price: float,
        current_equity: float,
    ) -> Dict[str, Any]:
        """
        Check if single position size exceeds limit.
        """
        position_value = abs(order_size * order_price)
        position_fraction = position_value / current_equity if current_equity > 0 else float('inf')
        
        if position_fraction > self.max_position_size:
            logger.warning(
                f"Position size {position_fraction:.1%} exceeds limit {self.max_position_size:.1%}"
            )
            
            # Calculate adjusted size
            max_value = current_equity * self.max_position_size
            adjusted_size = max_value / order_price if order_price > 0 else 0
            
            return {
                'allowed': False,
                'reason': f"Position size too large: {position_fraction:.1%} > {self.max_position_size:.1%}",
                'modified_size': adjusted_size,
            }
        
        return {'allowed': True}
    
    def _check_drawdowns(
        self,
        current_equity: float,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Check daily and total drawdown limits.
        """
        # Initialize or reset daily tracking
        current_date = timestamp.date()
        if self.last_reset_date != current_date:
            self.daily_start_equity = current_equity
            self.daily_high_watermark = current_equity
            self.last_reset_date = current_date
            logger.info(f"Daily reset: equity={current_equity:.2f}")
        
        # Update high watermarks
        if self.total_high_watermark is None or current_equity > self.total_high_watermark:
            self.total_high_watermark = current_equity
        
        if current_equity > self.daily_high_watermark:
            self.daily_high_watermark = current_equity
        
        # Calculate drawdowns
        daily_dd = 0.0
        if self.daily_high_watermark > 0:
            daily_dd = (self.daily_high_watermark - current_equity) / self.daily_high_watermark
        
        total_dd = 0.0
        if self.total_high_watermark > 0:
            total_dd = (self.total_high_watermark - current_equity) / self.total_high_watermark
        
        # Check daily drawdown
        if daily_dd > self.max_daily_drawdown:
            logger.error(
                f"🚨 DAILY DRAWDOWN LIMIT BREACHED: {daily_dd:.1%} > {self.max_daily_drawdown:.1%}"
            )
            return {
                'allowed': False,
                'reason': f"Daily drawdown limit exceeded: {daily_dd:.1%}",
                'daily_drawdown': daily_dd,
                'total_drawdown': total_dd,
            }
        
        # Check total drawdown
        if total_dd > self.max_total_drawdown:
            logger.error(
                f"🚨 TOTAL DRAWDOWN LIMIT BREACHED: {total_dd:.1%} > {self.max_total_drawdown:.1%}"
            )
            return {
                'allowed': False,
                'reason': f"Total drawdown limit exceeded: {total_dd:.1%}",
                'daily_drawdown': daily_dd,
                'total_drawdown': total_dd,
            }
        
        # Check hourly loss limit
        hourly_check = self._check_hourly_loss(current_equity, timestamp)
        if not hourly_check['allowed']:
            return hourly_check
        
        return {
            'allowed': True,
            'daily_drawdown': daily_dd,
            'total_drawdown': total_dd,
        }
    
    def _check_hourly_loss(
        self,
        current_equity: float,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Check hourly loss limit to prevent rapid equity erosion.
        """
        # Reset hourly tracking
        if self.last_hourly_reset is None or \
           (timestamp - self.last_hourly_reset).total_seconds() >= 3600:
            self.hourly_start_equity = current_equity
            self.last_hourly_reset = timestamp
        
        # Calculate hourly loss
        if self.hourly_start_equity and self.hourly_start_equity > 0:
            hourly_loss = (self.hourly_start_equity - current_equity) / self.hourly_start_equity
            
            if hourly_loss > self.max_hourly_loss:
                logger.error(
                    f"🚨 HOURLY LOSS LIMIT BREACHED: {hourly_loss:.1%} > {self.max_hourly_loss:.1%}"
                )
                return {
                    'allowed': False,
                    'reason': f"Hourly loss limit exceeded: {hourly_loss:.1%}",
                    'hourly_loss': hourly_loss,
                }
        
        return {'allowed': True}
    
    def _trip_breaker(self, reason: str, timestamp: datetime):
        """
        Trip the circuit breaker and halt trading.
        """
        self.is_tripped = True
        self.trip_reason = reason
        self.trip_time = timestamp
        
        logger.critical(f"⛔ CIRCUIT BREAKER TRIPPED: {reason} at {timestamp}")
        
        self._log_violation(f"CIRCUIT BREAKER TRIPPED: {reason}", timestamp)
    
    def _should_reset_breaker(self, current_time: datetime) -> bool:
        """
        Check if enough time has passed to reset breaker.
        """
        if not self.is_tripped or self.trip_time is None:
            return False
        
        elapsed = (current_time - self.trip_time).total_seconds() / 60
        return elapsed >= self.cooldown_period_minutes
    
    def _reset_breaker(self):
        """
        Reset the circuit breaker after cooldown.
        """
        logger.info(f"Resetting circuit breaker (was tripped: {self.trip_reason})")
        self.is_tripped = False
        self.trip_reason = None
        self.trip_time = None
    
    def _log_violation(
        self,
        reason: str,
        timestamp: datetime,
        order_details: Optional[Dict] = None,
    ):
        """
        Log a violation for audit trail.
        """
        violation = {
            'timestamp': timestamp,
            'reason': reason,
            'order_details': order_details,
        }
        self.violation_log.append(violation)
        
        logger.warning(f"Risk violation logged: {reason}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'is_tripped': self.is_tripped,
            'trip_reason': self.trip_reason,
            'trip_time': self.trip_time,
            'violations_count': len(self.violation_log),
            'daily_high_watermark': self.daily_high_watermark,
            'total_high_watermark': self.total_high_watermark,
            'last_reset_date': self.last_reset_date,
        }
    
    def get_violation_log(self) -> list:
        """
        Get full violation log for audit.
        
        Returns:
            List of violation dictionaries
        """
        return self.violation_log.copy()
    
    def export_violation_log(self, filepath: str):
        """
        Export violation log to CSV for audit trail.
        
        Args:
            filepath: Path to save CSV file
        """
        if not self.violation_log:
            logger.info("No violations to export")
            return
        
        df = pd.DataFrame(self.violation_log)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(self.violation_log)} violations to {filepath}")
    
    def manual_reset(self):
        """
        Manually reset the circuit breaker (use with caution).
        """
        logger.warning("⚠️  Manual circuit breaker reset requested")
        self._reset_breaker()
        logger.info("Circuit breaker manually reset")
