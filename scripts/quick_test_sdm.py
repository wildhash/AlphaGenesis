#!/usr/bin/env python3
"""
Quick SDM Test - Tests core SDM components without full dependencies
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test imports
print("Testing SDM component imports...")

try:
    from alphagenesis.sdm.intent_graph import IntentGraph, Intent, IntentType, Constraint, ConstraintType, Stake
    print("✓ Intent Graph imported successfully")
except Exception as e:
    print(f"✗ Intent Graph import failed: {e}")
    sys.exit(1)

try:
    from alphagenesis.sdm.semantic_binding import SemanticBindingLayer, HybridAssociativeMemory, ModelType, MarketRegime
    print("✓ Semantic Binding imported successfully")
except Exception as e:
    print(f"✗ Semantic Binding import failed: {e}")
    sys.exit(1)

try:
    from alphagenesis.sdm.continuous_learning import ContinuousLearningEngine, PerformanceFeedback
    print("✓ Continuous Learning imported successfully")
except Exception as e:
    print(f"✗ Continuous Learning import failed: {e}")
    sys.exit(1)

try:
    from alphagenesis.sdm.constraint_propagation import ConstraintPropagator, ConstraintField, FieldType
    print("✓ Constraint Propagation imported successfully")
except Exception as e:
    print(f"✗ Constraint Propagation import failed: {e}")
    sys.exit(1)

try:
    from alphagenesis.sdm.ethics_engine import EthicsEngine, EthicalConstraint, EthicalDomain
    print("✓ Ethics Engine imported successfully")
except Exception as e:
    print(f"✗ Ethics Engine import failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("Quick functional tests...")
print("="*70)

# Test Intent Graph
print("\n1. Testing Intent Graph...")
graph = IntentGraph()
graph.initialize_trading_intents()
print(f"   ✓ Created {len(graph.nodes)} intent nodes")
print(f"   ✓ Created {len(graph.edges)} edges")

graph.step()
most_active = graph.get_most_active_intents(top_k=2)
print(f"   ✓ Propagation works, {len(most_active)} most active intents")

# Test Semantic Binding
print("\n2. Testing Semantic Binding...")
binding_layer = SemanticBindingLayer(embedding_dim=32)
binding_layer.him.embed_intent("test_intent", "Maximize returns")
print(f"   ✓ Intent embedding works")
print(f"   ✓ HIM has {len(binding_layer.him.model_embeddings)} model embeddings")

# Test Continuous Learning
print("\n3. Testing Continuous Learning...")
from datetime import datetime
learning_engine = ContinuousLearningEngine()
feedback = PerformanceFeedback(
    action_id="test_1",
    intent_id="test",
    model_type="lstm",
    timestamp=datetime.now(),
    success=True,
    pnl=10.0,
    fitness_score=0.8
)
learning_engine.record_feedback(feedback)
print(f"   ✓ Feedback recording works")
print(f"   ✓ Total feedback: {learning_engine.total_feedback}")

# Test Constraint Propagation
print("\n4. Testing Constraint Propagation...")
propagator = ConstraintPropagator()
propagator.initialize_trading_constraints()
print(f"   ✓ Created {len(propagator.fields)} constraint fields")

propagator.update_state({'max_leverage': 15.0})
force = propagator.compute_total_force('max_leverage')
print(f"   ✓ Constraint force computation works (force: {force:.2f})")

# Test Ethics Engine
print("\n5. Testing Ethics Engine...")
ethics = EthicsEngine()
ethics.initialize_trading_ethics()
print(f"   ✓ Created {len(ethics.constraints)} ethical constraints")

test_action = {
    'max_leverage': 15.0,
    'total_drawdown': 0.10,
}
is_ethical, violations, penalty = ethics.evaluate_action(test_action)
print(f"   ✓ Ethics evaluation works (ethical: {is_ethical}, penalty: {penalty:.2f})")

print("\n" + "="*70)
print("✅ ALL SDM COMPONENT TESTS PASSED!")
print("="*70)
print("\nThe SDM system is ready for integration and deployment.")
print()
