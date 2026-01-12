#!/usr/bin/env python3
"""Minimal SDM test - imports SDM modules directly"""

# Import SDM modules directly without going through alphagenesis.__init__
import sys
sys.path.insert(0, '/home/user/AlphaGenesis')

print("Testing SDM components...")
print("="*70)

# Test 1: Intent Graph
print("\n1. Intent Graph")
from alphagenesis.sdm.intent_graph import IntentGraph
graph = IntentGraph()
graph.initialize_trading_intents()
print(f"   ✓ Created {len(graph.nodes)} intent nodes, {len(graph.edges)} edges")

# Test 2: Semantic Binding
print("\n2. Semantic Binding Layer")
from alphagenesis.sdm.semantic_binding import SemanticBindingLayer, ModelType
binding = SemanticBindingLayer(embedding_dim=32)
binding.him.embed_intent("test", "Maximize returns")
print(f"   ✓ HIM initialized with {len(binding.him.model_embeddings)} model types")

# Test 3: Continuous Learning
print("\n3. Continuous Learning Engine")
from alphagenesis.sdm.continuous_learning import ContinuousLearningEngine, PerformanceFeedback
from datetime import datetime
learning = ContinuousLearningEngine()
feedback = PerformanceFeedback(
    action_id="test",
    intent_id="test",
    model_type="lstm",
    timestamp=datetime.now(),
    success=True,
    pnl=10.0,
    fitness_score=0.8
)
learning.record_feedback(feedback)
print(f"   ✓ Recorded {learning.total_feedback} feedback samples")

# Test 4: Constraint Propagation
print("\n4. Constraint Propagation")
from alphagenesis.sdm.constraint_propagation import ConstraintPropagator
propagator = ConstraintPropagator()
propagator.initialize_trading_constraints()
print(f"   ✓ Created {len(propagator.fields)} constraint fields")

# Test 5: Ethics Engine
print("\n5. Ethics Engine")
from alphagenesis.sdm.ethics_engine import EthicsEngine
ethics = EthicsEngine()
ethics.initialize_trading_ethics()
print(f"   ✓ Created {len(ethics.constraints)} ethical constraints")

test_action = {'max_leverage': 15.0, 'total_drawdown': 0.10}
is_ethical, violations, penalty = ethics.evaluate_action(test_action)
print(f"   ✓ Ethics check: ethical={is_ethical}, penalty={penalty:.2f}")

print("\n" + "="*70)
print("✅ ALL SDM COMPONENTS WORKING!")
print("="*70)
print("\nSDM System Status:")
print(f"  - Intent Graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
print(f"  - Semantic Binding: {len(binding.him.model_embeddings)} model types")
print(f"  - Learning Engine: {learning.total_feedback} feedbacks tracked")
print(f"  - Constraint Fields: {len(propagator.fields)} fields active")
print(f"  - Ethical Constraints: {len(ethics.constraints)} constraints")
print("\n🎉 SDM is ready for the WEEX AI Wars Hackathon!")
print()
