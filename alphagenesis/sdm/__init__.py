"""
Semantic Dataflow Machine (SDM) - Intent-Driven Trading System

This module implements a post-Von Neumann computational paradigm where:
- Intent replaces instructions
- Semantic binding replaces compilation
- Continuous resolution replaces execution
- Learning is embodied in the dataflow

Core Components:
- IntentGraph: Represents trading goals, constraints, and their relationships
- SemanticBindingLayer: Dynamically binds intent to models/strategies
- ContinuousLearning: Adapts strategies based on performance
- ConstraintPropagation: Ensures all limits are respected
- EthicsEngine: First-class ethical constraints
"""

from .intent_graph import IntentGraph, Intent, IntentNode, Constraint, Stake
from .semantic_binding import SemanticBindingLayer, HybridAssociativeMemory
from .continuous_learning import ContinuousLearningEngine, PerformanceFeedback
from .constraint_propagation import ConstraintPropagator, ConstraintField
from .ethics_engine import EthicsEngine, EthicalConstraint
from .sdm_engine import SDMTradingEngine

__all__ = [
    'IntentGraph',
    'Intent',
    'IntentNode',
    'Constraint',
    'Stake',
    'SemanticBindingLayer',
    'HybridAssociativeMemory',
    'ContinuousLearningEngine',
    'PerformanceFeedback',
    'ConstraintPropagator',
    'ConstraintField',
    'EthicsEngine',
    'EthicalConstraint',
    'SDMTradingEngine',
]
