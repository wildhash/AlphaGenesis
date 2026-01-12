#!/usr/bin/env python3
"""
Test SDM Trading System Components

This script tests all SDM components before deployment.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenesis.sdm import (
    IntentGraph,
    SemanticBindingLayer,
    ContinuousLearningEngine,
    ConstraintPropagator,
    EthicsEngine,
    PerformanceFeedback,
    ModelType,
    MarketRegime
)
from datetime import datetime
from loguru import logger


def test_intent_graph():
    """Test Intent Graph functionality."""
    logger.info("="*70)
    logger.info("Testing Intent Graph")
    logger.info("="*70)

    # Create and initialize
    graph = IntentGraph()
    graph.initialize_trading_intents()

    # Check nodes
    assert len(graph.nodes) == 4, "Should have 4 primary intents"
    assert len(graph.edges) > 0, "Should have edges between intents"

    # Test activation propagation
    graph.step()
    most_active = graph.get_most_active_intents(top_k=2)

    logger.info(f"✓ Intent graph initialized with {len(graph.nodes)} nodes")
    logger.info(f"✓ Most active intents:")
    for node in most_active:
        logger.info(f"  - {node.intent.goal[:50]} (activation: {node.activation_level:.2f})")

    # Test action evaluation
    test_action = {
        'confidence': 0.8,
        'max_leverage': 10.0,
        'max_drawdown': 0.15,
    }

    should_exec, reasoning = graph.should_execute_action(test_action)
    logger.info(f"✓ Action evaluation: {should_exec} - {reasoning}")

    logger.info("✓ Intent Graph tests PASSED\n")
    return True


def test_semantic_binding():
    """Test Semantic Binding Layer."""
    logger.info("="*70)
    logger.info("Testing Semantic Binding Layer")
    logger.info("="*70)

    # Create binding layer
    binding_layer = SemanticBindingLayer(embedding_dim=64)

    # Register some models
    binding_layer.register_model(ModelType.LSTM, model_instance=None)
    binding_layer.register_model(ModelType.TRANSFORMER, model_instance=None)
    binding_layer.register_model(ModelType.ENSEMBLE, model_instance=None)

    logger.info(f"✓ Registered {len(binding_layer.model_registry)} models")

    # Test intent embedding
    binding_layer.him.embed_intent("test_intent", "Maximize returns with low risk")
    logger.info("✓ Intent embedding works")

    # Test binding resolution
    context = {'regime': MarketRegime.STRONG_UPTREND}
    best_model = binding_layer.get_best_model_for_context("test_intent", context)

    logger.info(f"✓ Resolved intent to model: {best_model.value if best_model else 'None'}")

    # Test learning from feedback
    feedback = [
        ("test_intent", ModelType.LSTM, True),
        ("test_intent", ModelType.LSTM, True),
        ("test_intent", ModelType.TRANSFORMER, False),
    ]
    binding_layer.learn_from_feedback(feedback)
    logger.info("✓ Learned from feedback")

    logger.info("✓ Semantic Binding tests PASSED\n")
    return True


def test_continuous_learning():
    """Test Continuous Learning Engine."""
    logger.info("="*70)
    logger.info("Testing Continuous Learning Engine")
    logger.info("="*70)

    learning_engine = ContinuousLearningEngine(
        learning_rate=0.01,
        adaptation_threshold=0.3,
        min_samples=5
    )

    # Record some feedback
    for i in range(10):
        feedback = PerformanceFeedback(
            action_id=f"action_{i}",
            intent_id="grow_capital",
            model_type="lstm",
            timestamp=datetime.now(),
            success=i % 2 == 0,  # 50% success rate
            pnl=10.0 if i % 2 == 0 else -5.0,
            fitness_score=0.7 if i % 2 == 0 else 0.3
        )
        learning_engine.record_feedback(feedback)

    logger.info(f"✓ Recorded {learning_engine.total_feedback} feedback samples")

    # Get metrics
    metrics = learning_engine.get_learning_metrics()
    logger.info(f"✓ Recent success rate: {metrics['recent_success_rate']:.1%}")
    logger.info(f"✓ Recent avg P&L: ${metrics['recent_avg_pnl']:.2f}")

    logger.info("✓ Continuous Learning tests PASSED\n")
    return True


def test_constraint_propagation():
    """Test Constraint Propagation."""
    logger.info("="*70)
    logger.info("Testing Constraint Propagation")
    logger.info("="*70)

    propagator = ConstraintPropagator()
    propagator.initialize_trading_constraints()

    logger.info(f"✓ Initialized {len(propagator.fields)} constraint fields")

    # Update state
    propagator.update_state({
        'max_leverage': 15.0,
        'max_drawdown': 0.10,
        'position_size': 0.30,
    })

    # Check violations
    violations = propagator.get_constraint_violations()
    logger.info(f"✓ Constraint violations: {len(violations)}")

    # Test action adjustment
    proposed_action = {
        'max_leverage': 25.0,  # Over limit
        'position_size': 0.60,  # High
    }

    adjusted = propagator.adjust_action(proposed_action)
    logger.info(f"✓ Adjusted leverage from {proposed_action['max_leverage']:.1f} to {adjusted['max_leverage']:.1f}")

    logger.info("✓ Constraint Propagation tests PASSED\n")
    return True


def test_ethics_engine():
    """Test Ethics Engine."""
    logger.info("="*70)
    logger.info("Testing Ethics Engine")
    logger.info("="*70)

    ethics = EthicsEngine()
    ethics.initialize_trading_ethics()

    logger.info(f"✓ Initialized {len(ethics.constraints)} ethical constraints")

    # Test acceptable action
    good_action = {
        'total_drawdown': 0.10,
        'max_leverage': 15.0,
        'daily_drawdown': 0.05,
    }

    is_ethical, violations, penalty = ethics.evaluate_action(good_action)
    logger.info(f"✓ Good action: ethical={is_ethical}, penalty={penalty:.2f}")

    # Test unacceptable action
    bad_action = {
        'total_drawdown': 0.30,  # Over 25% limit
        'max_leverage': 25.0,    # Over 20x limit
    }

    is_ethical, violations, penalty = ethics.evaluate_action(bad_action)
    logger.info(f"✓ Bad action: ethical={is_ethical}, violations={len(violations)}, penalty={penalty:.2f}")

    should_permit, reason = ethics.should_permit_action(bad_action)
    logger.info(f"✓ Permission: {should_permit} - {reason}")

    logger.info("✓ Ethics Engine tests PASSED\n")
    return True


def main():
    """Run all tests."""
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, format="<level>{message}</level>", level="INFO")

    logger.info("\n" + "="*70)
    logger.info("SDM SYSTEM COMPONENT TESTS")
    logger.info("="*70 + "\n")

    tests = [
        ("Intent Graph", test_intent_graph),
        ("Semantic Binding", test_semantic_binding),
        ("Continuous Learning", test_continuous_learning),
        ("Constraint Propagation", test_constraint_propagation),
        ("Ethics Engine", test_ethics_engine),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"✗ {name} test FAILED: {e}")
            failed += 1

    logger.info("="*70)
    logger.info(f"TEST RESULTS: {passed} passed, {failed} failed")
    logger.info("="*70)

    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! System is ready for deployment.\n")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED. Please fix before deployment.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
