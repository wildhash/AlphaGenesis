"""
Constraint Propagation - Constraints as Potential Fields

Constraints are not rules or if-statements.
Constraints are FIELDS that apply continuous pressure.

Think: Potential fields, not if-statements.
Violations don't crash - they REPEL.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
import numpy as np
from loguru import logger


class FieldType(Enum):
    """Types of constraint fields."""
    ATTRACTIVE = "attractive"  # Pulls toward desired state
    REPULSIVE = "repulsive"  # Pushes away from undesired state
    BOUNDARY = "boundary"  # Hard boundary (infinite repulsion)


@dataclass
class ConstraintField:
    """
    A constraint field in state space.

    Like a potential field in physics - exerts force on the system.
    """
    name: str
    field_type: FieldType
    center: float  # The target or boundary value
    strength: float  # Field strength
    falloff: float = 2.0  # How quickly field strength decreases (power law)
    is_active: bool = True

    def compute_force(self, current_value: float) -> float:
        """
        Compute force exerted by this field at current value.

        Returns:
            Force magnitude (positive = repulsion, negative = attraction)
        """
        if not self.is_active:
            return 0.0

        distance = current_value - self.center

        if self.field_type == FieldType.BOUNDARY:
            # Hard boundary - infinite repulsion if crossed
            if abs(distance) < 1e-6:
                return 0.0
            if distance > 0:  # Crossed boundary
                return 1e6 * self.strength
            return -self.strength * 0.1  # Slight attraction toward boundary

        elif self.field_type == FieldType.REPULSIVE:
            # Repulsive field - stronger as you get closer
            if abs(distance) < 1e-6:
                return 0.0
            force = self.strength / (abs(distance) ** self.falloff)
            return force if distance > 0 else -force

        elif self.field_type == FieldType.ATTRACTIVE:
            # Attractive field - pulls toward center
            if abs(distance) < 1e-6:
                return 0.0
            force = self.strength * (abs(distance) ** (self.falloff - 1))
            return -force if distance > 0 else force

        return 0.0

    def compute_potential(self, current_value: float) -> float:
        """
        Compute potential energy at current value.

        Returns:
            Potential energy (higher = worse)
        """
        if not self.is_active:
            return 0.0

        distance = abs(current_value - self.center)

        if self.field_type == FieldType.BOUNDARY:
            if current_value > self.center:
                return 1e6  # Infinite potential if boundary crossed
            return distance * self.strength * 0.1

        elif self.field_type == FieldType.REPULSIVE:
            if distance < 1e-6:
                return 1e6
            return self.strength / (distance ** (self.falloff - 1))

        elif self.field_type == FieldType.ATTRACTIVE:
            return self.strength * (distance ** self.falloff)

        return 0.0


class ConstraintPropagator:
    """
    Constraint Propagation Engine.

    Manages a field of constraints that continuously influence decisions.
    No if-statements. Just forces and potentials.
    """

    def __init__(self):
        """Initialize constraint propagator."""
        self.fields: Dict[str, ConstraintField] = {}
        self.state: Dict[str, float] = {}  # Current system state
        self.history: List[Dict[str, float]] = []  # State history
        logger.info("Constraint Propagator initialized")

    def add_field(
        self,
        name: str,
        field_type: FieldType,
        center: float,
        strength: float,
        falloff: float = 2.0
    ):
        """Add a constraint field."""
        field = ConstraintField(
            name=name,
            field_type=field_type,
            center=center,
            strength=strength,
            falloff=falloff
        )
        self.fields[name] = field
        logger.info(f"Added {field_type.value} field: {name} (center: {center}, strength: {strength})")

    def update_state(self, state_updates: Dict[str, float]):
        """Update current system state."""
        self.state.update(state_updates)
        self.history.append(self.state.copy())

        # Trim history
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def compute_total_force(self, state_var: str) -> float:
        """
        Compute total force on a state variable from all fields.

        Returns:
            Net force (positive = increase, negative = decrease)
        """
        if state_var not in self.state:
            return 0.0

        current_value = self.state[state_var]
        total_force = 0.0

        for field_name, field in self.fields.items():
            if field_name == state_var or field_name.startswith(state_var):
                force = field.compute_force(current_value)
                total_force += force

        return total_force

    def compute_total_potential(self) -> float:
        """
        Compute total potential energy of current state.

        Higher potential = worse state (more constraint violations).
        """
        total_potential = 0.0

        for state_var, value in self.state.items():
            for field_name, field in self.fields.items():
                if field_name == state_var or field_name.startswith(state_var):
                    potential = field.compute_potential(value)
                    total_potential += potential

        return total_potential

    def is_state_acceptable(self, threshold: float = 1000.0) -> bool:
        """
        Check if current state is acceptable.

        Args:
            threshold: Maximum acceptable potential energy

        Returns:
            True if state is acceptable
        """
        total_potential = self.compute_total_potential()
        return total_potential < threshold

    def adjust_action(self, proposed_action: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust a proposed action based on constraint fields.

        This is the key method - actions are SHAPED by constraints, not blocked.
        """
        adjusted = proposed_action.copy()

        for var_name, proposed_value in proposed_action.items():
            # Temporarily update state to proposed value
            original_value = self.state.get(var_name, 0.0)
            self.state[var_name] = proposed_value

            # Compute force
            force = self.compute_total_force(var_name)

            # If strong repulsive force, scale back the action
            if force > 100:  # Strong repulsion
                # Scale back toward original value
                scale_factor = 100 / (force + 100)
                adjusted[var_name] = original_value + (proposed_value - original_value) * scale_factor

                logger.warning(
                    f"Constraint repulsion on {var_name}: "
                    f"force={force:.2f}, scaled to {adjusted[var_name]:.4f}"
                )

            # Restore original value
            self.state[var_name] = original_value

        return adjusted

    def gradient_descent_step(
        self,
        learning_rate: float = 0.1
    ) -> Dict[str, float]:
        """
        Perform gradient descent on potential energy.

        Move state toward lower potential (better constraint satisfaction).
        """
        gradients = {}

        for state_var in self.state.keys():
            force = self.compute_total_force(state_var)
            # Force points in direction of increasing value
            # Negative force = should decrease, positive = should increase
            gradients[state_var] = -force * learning_rate

        # Update state
        new_state = {}
        for var, gradient in gradients.items():
            new_state[var] = self.state[var] + gradient

        return new_state

    def get_constraint_violations(self) -> List[Dict[str, Any]]:
        """Get list of current constraint violations."""
        violations = []

        for field_name, field in self.fields.items():
            if field.field_type == FieldType.BOUNDARY:
                for state_var, value in self.state.items():
                    if field_name == state_var or field_name.startswith(state_var):
                        if value > field.center:
                            violations.append({
                                'field': field_name,
                                'type': 'HARD_BOUNDARY',
                                'current': value,
                                'limit': field.center,
                                'severity': 'CRITICAL'
                            })

            elif field.field_type == FieldType.REPULSIVE:
                for state_var, value in self.state.items():
                    if field_name == state_var or field_name.startswith(state_var):
                        force = field.compute_force(value)
                        if force > 10:  # Significant repulsion
                            violations.append({
                                'field': field_name,
                                'type': 'SOFT_CONSTRAINT',
                                'current': value,
                                'target': field.center,
                                'force': force,
                                'severity': 'WARNING' if force < 100 else 'HIGH'
                            })

        return violations

    def initialize_trading_constraints(self):
        """
        Initialize constraint fields for trading.

        This creates the potential field landscape for the trading system.
        """
        # Hard boundaries (NEVER cross)
        self.add_field(
            name="max_leverage",
            field_type=FieldType.BOUNDARY,
            center=20.0,  # Hackathon limit
            strength=1000.0,
            falloff=1.0
        )

        self.add_field(
            name="max_drawdown",
            field_type=FieldType.BOUNDARY,
            center=0.25,  # 25% max drawdown
            strength=1000.0,
            falloff=1.0
        )

        self.add_field(
            name="daily_drawdown",
            field_type=FieldType.BOUNDARY,
            center=0.10,  # 10% daily
            strength=500.0,
            falloff=1.0
        )

        # Soft constraints (repulsive fields)
        self.add_field(
            name="position_size",
            field_type=FieldType.REPULSIVE,
            center=0.50,  # Start repelling above 50% position
            strength=10.0,
            falloff=2.0
        )

        self.add_field(
            name="daily_trades",
            field_type=FieldType.REPULSIVE,
            center=3.0,  # Repel more than 3 trades/day
            strength=20.0,
            falloff=3.0
        )

        # Attractive fields (pull toward desirable states)
        self.add_field(
            name="risk_reward_ratio",
            field_type=FieldType.ATTRACTIVE,
            center=3.0,  # Pull toward 3:1 R:R
            strength=5.0,
            falloff=1.5
        )

        self.add_field(
            name="cash_reserve",
            field_type=FieldType.ATTRACTIVE,
            center=0.20,  # Pull toward 20% cash
            strength=3.0,
            falloff=2.0
        )

        logger.info("Trading constraint fields initialized")

    def get_field_visualization(self) -> Dict[str, Any]:
        """Get data for visualizing constraint fields."""
        visualization = {}

        for field_name, field in self.fields.items():
            # Sample the field at different values
            values = np.linspace(0, field.center * 2, 50)
            forces = [field.compute_force(v) for v in values]
            potentials = [field.compute_potential(v) for v in values]

            visualization[field_name] = {
                'type': field.field_type.value,
                'center': field.center,
                'strength': field.strength,
                'current_value': self.state.get(field_name, 0.0),
                'current_force': field.compute_force(self.state.get(field_name, 0.0)),
                'current_potential': field.compute_potential(self.state.get(field_name, 0.0)),
                'sample_values': values.tolist(),
                'sample_forces': forces,
                'sample_potentials': potentials,
            }

        return visualization
