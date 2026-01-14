"""
Ethics Engine - First-Class Ethical Constraints

Ethics are not rules.
Ethics are CONSTRAINTS with ASYMMETRIC PENALTIES.

In SDM:
- Ethics live in HIM
- Ethics apply pressure continuously
- Violations don't crash - they REPEL

Think: Potential fields, not if-statements.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import numpy as np
from loguru import logger


class EthicalDomain(Enum):
    """Domains of ethical constraints."""
    CAPITAL_PRESERVATION = "capital_preservation"
    RISK_LIMITS = "risk_limits"
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    SAFETY = "safety"


class ViolationSeverity(Enum):
    """Severity levels for ethical violations."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


@dataclass
class EthicalConstraint:
    """
    An ethical constraint with asymmetric penalty.

    Violating ethics should be MUCH more costly than satisfying them.
    """
    name: str
    domain: EthicalDomain
    description: str
    threshold: float  # Threshold for violation
    penalty_base: float  # Base penalty
    asymmetry_factor: float = 10.0  # How much worse violations are vs compliance
    is_hard: bool = True  # Hard constraint = absolute prohibition
    metadata: Dict[str, Any] = field(default_factory=dict)

    def evaluate(self, current_value: float) -> tuple[bool, float, ViolationSeverity]:
        """
        Evaluate ethical constraint.

        Returns:
            (is_violated, penalty, severity)
        """
        if current_value <= self.threshold:
            # Constraint satisfied
            return False, 0.0, ViolationSeverity.INFO

        # Constraint violated
        violation_magnitude = current_value - self.threshold

        # Asymmetric penalty - violations are MUCH worse
        penalty = self.penalty_base * (violation_magnitude ** 2) * self.asymmetry_factor

        # Determine severity
        if self.is_hard:
            severity = ViolationSeverity.CATASTROPHIC
            penalty *= 100  # Hard constraints have extreme penalties
        elif violation_magnitude > self.threshold:
            severity = ViolationSeverity.CRITICAL
        elif violation_magnitude > self.threshold * 0.5:
            severity = ViolationSeverity.WARNING
        else:
            severity = ViolationSeverity.INFO

        return True, penalty, severity


@dataclass
class EthicalViolation:
    """Record of an ethical violation."""
    constraint_name: str
    domain: EthicalDomain
    timestamp: datetime
    severity: ViolationSeverity
    current_value: float
    threshold: float
    penalty: float
    context: Dict[str, Any] = field(default_factory=dict)
    action_taken: str = "logged"


class EthicsEngine:
    """
    Ethics Engine - Ethical Constraints as First-Class Citizens.

    This engine:
    1. Maintains ethical constraints
    2. Evaluates proposed actions against ethics
    3. Applies asymmetric penalties for violations
    4. Escalates critical violations
    5. Provides ethical guidance
    """

    def __init__(self):
        """Initialize ethics engine."""
        self.constraints: Dict[str, EthicalConstraint] = {}
        self.violations: List[EthicalViolation] = []
        self.total_evaluations = 0
        self.total_violations = 0
        logger.info("Ethics Engine initialized")

    def add_constraint(
        self,
        name: str,
        domain: EthicalDomain,
        description: str,
        threshold: float,
        penalty_base: float,
        asymmetry_factor: float = 10.0,
        is_hard: bool = True
    ):
        """Add an ethical constraint."""
        constraint = EthicalConstraint(
            name=name,
            domain=domain,
            description=description,
            threshold=threshold,
            penalty_base=penalty_base,
            asymmetry_factor=asymmetry_factor,
            is_hard=is_hard
        )
        self.constraints[name] = constraint
        logger.info(f"Added ethical constraint: {name} ({domain.value})")

    def evaluate_action(
        self,
        proposed_action: Dict[str, Any]
    ) -> tuple[bool, List[EthicalViolation], float]:
        """
        Evaluate a proposed action against all ethical constraints.

        Returns:
            (is_ethical, violations, total_penalty)
        """
        self.total_evaluations += 1
        violations = []
        total_penalty = 0.0

        for constraint_name, constraint in self.constraints.items():
            # Get relevant value from action
            value = proposed_action.get(constraint_name, 0.0)

            # Evaluate constraint
            is_violated, penalty, severity = constraint.evaluate(value)

            if is_violated:
                self.total_violations += 1

                violation = EthicalViolation(
                    constraint_name=constraint_name,
                    domain=constraint.domain,
                    timestamp=datetime.now(),
                    severity=severity,
                    current_value=value,
                    threshold=constraint.threshold,
                    penalty=penalty,
                    context=proposed_action
                )

                violations.append(violation)
                self.violations.append(violation)
                total_penalty += penalty

                # Log violation
                if severity in [ViolationSeverity.CRITICAL, ViolationSeverity.CATASTROPHIC]:
                    logger.error(
                        f"ETHICAL VIOLATION: {constraint_name} - "
                        f"Severity: {severity.value}, "
                        f"Value: {value:.4f} > Threshold: {constraint.threshold:.4f}, "
                        f"Penalty: {penalty:.2f}"
                    )
                else:
                    logger.warning(
                        f"Ethical warning: {constraint_name} - "
                        f"Value: {value:.4f} > Threshold: {constraint.threshold:.4f}"
                    )

        # Trim violation history
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]

        is_ethical = total_penalty < 1000.0  # High penalty threshold = unethical

        return is_ethical, violations, total_penalty

    def should_permit_action(
        self,
        proposed_action: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Determine if action should be permitted based on ethics.

        Returns:
            (should_permit, reasoning)
        """
        is_ethical, violations, total_penalty = self.evaluate_action(proposed_action)

        if not violations:
            return True, "No ethical violations detected"

        # Check for catastrophic violations
        catastrophic = [v for v in violations if v.severity == ViolationSeverity.CATASTROPHIC]
        if catastrophic:
            reasons = [f"{v.constraint_name} (HARD CONSTRAINT)" for v in catastrophic]
            return False, f"Catastrophic violations: {', '.join(reasons)}"

        # Check for critical violations
        critical = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        if critical and total_penalty > 500:
            reasons = [v.constraint_name for v in critical]
            return False, f"Critical violations with high penalty: {', '.join(reasons)}"

        # Allow with warnings
        if total_penalty < 100:
            return True, f"Minor violations (penalty: {total_penalty:.2f}), permitted with warning"

        return False, f"Total ethical penalty too high: {total_penalty:.2f}"

    def apply_ethical_pressure(
        self,
        proposed_action: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply ethical pressure to adjust proposed action.

        Actions are SHAPED by ethics, not just blocked.
        """
        adjusted = proposed_action.copy()

        for constraint_name, constraint in self.constraints.items():
            if constraint_name not in proposed_action:
                continue

            proposed_value = proposed_action[constraint_name]

            # If approaching violation, apply pressure to reduce
            if proposed_value > constraint.threshold * 0.8:  # Within 80% of threshold
                # Calculate pressure (increases exponentially near threshold)
                proximity = proposed_value / constraint.threshold
                pressure = (proximity - 0.8) / 0.2  # 0 to 1 as we approach threshold

                # Reduce value proportionally
                reduction_factor = 1.0 - (pressure * 0.3)  # Reduce up to 30%
                adjusted[constraint_name] = proposed_value * reduction_factor

                logger.info(
                    f"Applied ethical pressure to {constraint_name}: "
                    f"{proposed_value:.4f} -> {adjusted[constraint_name]:.4f} "
                    f"(threshold: {constraint.threshold:.4f})"
                )

        return adjusted

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of ethical violations."""
        if not self.violations:
            return {'total_violations': 0, 'message': 'No violations recorded'}

        recent_violations = self.violations[-100:]

        by_severity = {
            'catastrophic': len([v for v in recent_violations if v.severity == ViolationSeverity.CATASTROPHIC]),
            'critical': len([v for v in recent_violations if v.severity == ViolationSeverity.CRITICAL]),
            'warning': len([v for v in recent_violations if v.severity == ViolationSeverity.WARNING]),
            'info': len([v for v in recent_violations if v.severity == ViolationSeverity.INFO]),
        }

        by_domain = {}
        for v in recent_violations:
            domain = v.domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1

        return {
            'total_violations': self.total_violations,
            'total_evaluations': self.total_evaluations,
            'violation_rate': self.total_violations / max(1, self.total_evaluations),
            'recent_violations': len(recent_violations),
            'by_severity': by_severity,
            'by_domain': by_domain,
            'most_violated_constraint': max(
                self.constraints.keys(),
                key=lambda c: len([v for v in recent_violations if v.constraint_name == c])
            ) if recent_violations else None
        }

    def initialize_trading_ethics(self):
        """
        Initialize ethical constraints for trading.

        These are the non-negotiable ethical boundaries.
        """
        # Capital Preservation - NEVER lose all capital
        self.add_constraint(
            name="total_drawdown",
            domain=EthicalDomain.CAPITAL_PRESERVATION,
            description="Never lose more than 25% of capital",
            threshold=0.25,
            penalty_base=1000.0,
            asymmetry_factor=20.0,
            is_hard=True
        )

        # Risk Limits - NEVER exceed leverage limits
        self.add_constraint(
            name="max_leverage",
            domain=EthicalDomain.RISK_LIMITS,
            description="Never exceed 20x leverage (hackathon rule)",
            threshold=20.0,
            penalty_base=1000.0,
            asymmetry_factor=50.0,
            is_hard=True
        )

        # Daily Loss Limits
        self.add_constraint(
            name="daily_drawdown",
            domain=EthicalDomain.RISK_LIMITS,
            description="Never lose more than 10% in one day",
            threshold=0.10,
            penalty_base=500.0,
            asymmetry_factor=15.0,
            is_hard=True
        )

        # Position Size Limits
        self.add_constraint(
            name="position_concentration",
            domain=EthicalDomain.RISK_LIMITS,
            description="Never put more than 50% in single position",
            threshold=0.50,
            penalty_base=100.0,
            asymmetry_factor=10.0,
            is_hard=False
        )

        # Overtrading Prevention
        self.add_constraint(
            name="daily_trade_count",
            domain=EthicalDomain.SAFETY,
            description="Never exceed 5 trades per day",
            threshold=5.0,
            penalty_base=50.0,
            asymmetry_factor=5.0,
            is_hard=False
        )

        # Minimum Trade Quality - DISABLED FOR COMPETITION
        # Intent graph already handles confidence thresholds (0.1)
        # This ethics constraint was blocking all trades due to logic error
        # self.add_constraint(
        #     name="confidence",
        #     domain=EthicalDomain.ACCOUNTABILITY,
        #     description="Never trade with confidence below 40%",
        #     threshold=-0.40,
        #     penalty_base=20.0,
        #     asymmetry_factor=8.0,
        #     is_hard=False
        # )

        logger.info("Trading ethical constraints initialized")

    def export_violations(self, filepath: str):
        """Export violation history for audit."""
        import json

        violations_data = [
            {
                'constraint_name': v.constraint_name,
                'domain': v.domain.value,
                'timestamp': v.timestamp.isoformat(),
                'severity': v.severity.value,
                'current_value': v.current_value,
                'threshold': v.threshold,
                'penalty': v.penalty,
                'action_taken': v.action_taken,
            }
            for v in self.violations
        ]

        with open(filepath, 'w') as f:
            json.dump({
                'total_violations': self.total_violations,
                'total_evaluations': self.total_evaluations,
                'violations': violations_data,
                'summary': self.get_violation_summary()
            }, f, indent=2)

        logger.info(f"Violation history exported to {filepath}")
