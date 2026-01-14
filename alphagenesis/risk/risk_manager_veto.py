"""
Risk Manager - Final Veto Authority on All Trades

This is the "adult in the room" that prevents the system from blowing up,
even if strategies, models, and ethics all approve a trade.

CRITICAL: All trade intents must pass through approve() AFTER ledger check
and BEFORE order placement.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time


@dataclass
class AccountState:
    """Current account state for risk calculations."""
    balance: float
    equity: float
    margin_used: float
    unrealized_pnl: float
    daily_pnl: float
    peak_balance_today: float
    total_notional: float  # Sum of all position notionals


@dataclass
class TradeIntent:
    """Proposed trade from strategy."""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    size: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.5


@dataclass
class VetoReason:
    """Reason for trade veto."""
    rule: str
    severity: str  # 'HARD' or 'SOFT'
    message: str
    value: float
    limit: float


class RiskManagerVeto:
    """
    Final veto authority on all trades.

    NO TRADE can execute without passing risk_manager.approve().
    """

    def __init__(
        self,
        initial_balance: float = 1000.0,
        max_notional_per_symbol: float = 2000.0,
        max_total_notional: float = 5000.0,
        max_leverage: float = 15.0,
        max_margin_ratio: float = 0.80,  # 80% of balance
        max_daily_loss_pct: float = 0.10,  # 10% max daily loss
        max_total_drawdown_pct: float = 0.25,  # 25% max drawdown
        max_per_trade_risk_pct: float = 0.02,  # 2% per trade
        min_risk_reward_ratio: float = 1.5,  # Minimum 1.5:1 RR
        fee_churn_threshold: float = -0.01,  # If last N trades avg < -1%, throttle
        fee_churn_lookback: int = 10,
    ):
        self.initial_balance = initial_balance
        self.max_notional_per_symbol = max_notional_per_symbol
        self.max_total_notional = max_total_notional
        self.max_leverage = max_leverage
        self.max_margin_ratio = max_margin_ratio
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_total_drawdown_pct = max_total_drawdown_pct
        self.max_per_trade_risk_pct = max_per_trade_risk_pct
        self.min_risk_reward_ratio = min_risk_reward_ratio
        self.fee_churn_threshold = fee_churn_threshold
        self.fee_churn_lookback = fee_churn_lookback

        # State tracking
        self.recent_trades_pnl: List[float] = []  # Last N trade results
        self.symbol_exposure: Dict[str, float] = {}  # symbol -> notional
        self.last_veto_log_time = 0.0

        logger.info("RiskManagerVeto initialized with hard limits")

    def approve(
        self,
        trade_intent: TradeIntent,
        account_state: AccountState,
        open_positions: Dict[str, any]
    ) -> Tuple[bool, List[VetoReason]]:
        """
        Final veto check for trade intent.

        Returns:
            (approved, veto_reasons)

        If ANY hard veto triggers → trade BLOCKED
        """
        veto_reasons = []

        # Calculate trade notional
        notional = trade_intent.size * trade_intent.entry_price

        # 1. Check per-symbol notional limit
        current_symbol_notional = self.symbol_exposure.get(trade_intent.symbol, 0.0)
        if current_symbol_notional + notional > self.max_notional_per_symbol:
            veto_reasons.append(VetoReason(
                rule='max_notional_per_symbol',
                severity='HARD',
                message=f"Symbol notional would exceed limit",
                value=current_symbol_notional + notional,
                limit=self.max_notional_per_symbol
            ))

        # 2. Check total notional limit
        if account_state.total_notional + notional > self.max_total_notional:
            veto_reasons.append(VetoReason(
                rule='max_total_notional',
                severity='HARD',
                message=f"Total notional would exceed limit",
                value=account_state.total_notional + notional,
                limit=self.max_total_notional
            ))

        # 3. Check margin ratio
        if account_state.balance > 0:
            margin_ratio = account_state.margin_used / account_state.balance
            if margin_ratio > self.max_margin_ratio:
                veto_reasons.append(VetoReason(
                    rule='max_margin_ratio',
                    severity='HARD',
                    message=f"Margin ratio too high",
                    value=margin_ratio,
                    limit=self.max_margin_ratio
                ))

        # 4. Check daily loss limit
        if account_state.daily_pnl < 0:
            daily_loss_pct = abs(account_state.daily_pnl) / account_state.peak_balance_today
            if daily_loss_pct > self.max_daily_loss_pct:
                veto_reasons.append(VetoReason(
                    rule='max_daily_loss',
                    severity='HARD',
                    message=f"Daily loss limit exceeded",
                    value=daily_loss_pct,
                    limit=self.max_daily_loss_pct
                ))

        # 5. Check total drawdown limit
        drawdown = (self.initial_balance - account_state.balance) / self.initial_balance
        if drawdown > self.max_total_drawdown_pct:
            veto_reasons.append(VetoReason(
                rule='max_total_drawdown',
                severity='HARD',
                message=f"Total drawdown limit exceeded",
                value=drawdown,
                limit=self.max_total_drawdown_pct
            ))

        # 6. Check per-trade risk (if stop loss provided)
        if trade_intent.stop_loss:
            if trade_intent.side == 'LONG':
                risk_per_unit = abs(trade_intent.entry_price - trade_intent.stop_loss)
            else:  # SHORT
                risk_per_unit = abs(trade_intent.stop_loss - trade_intent.entry_price)

            total_risk = risk_per_unit * trade_intent.size
            risk_pct = total_risk / account_state.balance

            if risk_pct > self.max_per_trade_risk_pct:
                veto_reasons.append(VetoReason(
                    rule='max_per_trade_risk',
                    severity='HARD',
                    message=f"Trade risk exceeds per-trade limit",
                    value=risk_pct,
                    limit=self.max_per_trade_risk_pct
                ))

        # 7. Check risk/reward ratio (if both SL and TP provided)
        if trade_intent.stop_loss and trade_intent.take_profit:
            if trade_intent.side == 'LONG':
                risk = abs(trade_intent.entry_price - trade_intent.stop_loss)
                reward = abs(trade_intent.take_profit - trade_intent.entry_price)
            else:  # SHORT
                risk = abs(trade_intent.stop_loss - trade_intent.entry_price)
                reward = abs(trade_intent.entry_price - trade_intent.take_profit)

            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio < self.min_risk_reward_ratio:
                    veto_reasons.append(VetoReason(
                        rule='min_risk_reward',
                        severity='SOFT',  # Soft veto - can override if high confidence
                        message=f"Risk/reward ratio below minimum",
                        value=rr_ratio,
                        limit=self.min_risk_reward_ratio
                    ))

        # 8. Fee churn guard
        if len(self.recent_trades_pnl) >= self.fee_churn_lookback:
            avg_recent_pnl = sum(self.recent_trades_pnl[-self.fee_churn_lookback:]) / self.fee_churn_lookback
            avg_pnl_pct = avg_recent_pnl / account_state.balance

            if avg_pnl_pct < self.fee_churn_threshold:
                veto_reasons.append(VetoReason(
                    rule='fee_churn_guard',
                    severity='SOFT',
                    message=f"Recent trades showing negative expectancy",
                    value=avg_pnl_pct,
                    limit=self.fee_churn_threshold
                ))

        # Determine if trade is approved
        hard_vetoes = [r for r in veto_reasons if r.severity == 'HARD']
        approved = len(hard_vetoes) == 0

        # Log vetoes
        if not approved or veto_reasons:
            self._log_veto(trade_intent, approved, veto_reasons)

        return approved, veto_reasons

    def record_trade_result(self, realized_pnl: float):
        """Record trade result for churn detection."""
        self.recent_trades_pnl.append(realized_pnl)

        # Keep only recent history
        if len(self.recent_trades_pnl) > self.fee_churn_lookback * 2:
            self.recent_trades_pnl = self.recent_trades_pnl[-self.fee_churn_lookback:]

    def update_symbol_exposure(self, symbol: str, notional: float):
        """Update current exposure tracking."""
        self.symbol_exposure[symbol] = notional

    def _log_veto(self, trade_intent: TradeIntent, approved: bool, veto_reasons: List[VetoReason]):
        """Log veto decision."""
        now = time.time()

        # Throttle veto logs to avoid spam
        if now - self.last_veto_log_time < 60:  # Max 1/minute
            return

        if approved and veto_reasons:
            logger.warning(f"⚠️ RISK VETO (SOFT) for {trade_intent.symbol} {trade_intent.side}:")
            for reason in veto_reasons:
                logger.warning(f"   - {reason.rule}: {reason.message} "
                             f"(value={reason.value:.4f}, limit={reason.limit:.4f})")
        elif not approved:
            logger.error(f"❌ RISK VETO (HARD) for {trade_intent.symbol} {trade_intent.side}:")
            for reason in veto_reasons:
                logger.error(f"   - {reason.rule}: {reason.message} "
                           f"(value={reason.value:.4f}, limit={reason.limit:.4f})")

        self.last_veto_log_time = now

    def get_status(self) -> Dict:
        """Get risk manager status."""
        avg_recent = 0.0
        if self.recent_trades_pnl:
            avg_recent = sum(self.recent_trades_pnl[-self.fee_churn_lookback:]) / min(len(self.recent_trades_pnl), self.fee_churn_lookback)

        return {
            'recent_trades_count': len(self.recent_trades_pnl),
            'avg_recent_pnl': avg_recent,
            'symbol_exposure': dict(self.symbol_exposure),
            'limits': {
                'max_notional_per_symbol': self.max_notional_per_symbol,
                'max_total_notional': self.max_total_notional,
                'max_leverage': self.max_leverage,
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'max_total_drawdown_pct': self.max_total_drawdown_pct
            }
        }
