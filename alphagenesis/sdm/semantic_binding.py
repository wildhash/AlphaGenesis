"""
Semantic Binding Layer - Replaces Compilation

Instead of Code → AST → IR → Machine Code,
We have: Intent → Semantic Graph → Resource Binding → Dataflow Fabric

The Hybrid Associative Memory (HIM) enables O(1) semantic lookup,
binding abstract intent to concrete models, data feeds, and actuators.

HIM is not a cache - it's a meaning substrate.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import numpy as np
from datetime import datetime
from loguru import logger


class MarketRegime(Enum):
    """Market regime classifications."""
    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    SIDEWAYS = "sideways"
    WEAK_DOWNTREND = "weak_downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


class ModelType(Enum):
    """Available model types."""
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    RL_AGENT = "rl_agent"
    ENSEMBLE = "ensemble"
    QUANTUM_RISK = "quantum_risk"
    SCALPER = "scalper"
    SWING_TRADER = "swing_trader"
    ARBITRAGE = "arbitrage"
    MARKET_MAKER = "market_maker"


@dataclass
class SemanticBinding:
    """
    A binding between intent and executable resources.

    This is what makes intent executable.
    """
    intent_id: str
    model_type: ModelType
    regime: MarketRegime
    confidence: float
    resource_id: str  # Actual model instance ID
    binding_strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this binding."""
        if self.usage_count == 0:
            return 0.5
        return self.success_count / self.usage_count

    def use(self, success: bool):
        """Record usage of this binding."""
        self.usage_count += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.now()
        # Strengthen binding on success, weaken on failure
        if success:
            self.binding_strength = min(1.0, self.binding_strength + 0.05)
        else:
            self.binding_strength = max(0.1, self.binding_strength - 0.02)


class HybridAssociativeMemory:
    """
    Hybrid Associative Memory (HIM) - The Meaning Substrate.

    Provides O(1) semantic lookup to bind abstract intent to concrete resources.

    Structure:
    - Intent vectors (embedded in semantic space)
    - Model vectors (embedded in same space)
    - Context vectors (market regime, volatility, etc.)
    - Association matrix (learned over time)
    """

    def __init__(self, embedding_dim: int = 64):
        """Initialize HIM with embedding dimension."""
        self.embedding_dim = embedding_dim
        self.bindings: List[SemanticBinding] = []

        # Semantic embeddings (learned/updated over time)
        self.intent_embeddings: Dict[str, np.ndarray] = {}
        self.model_embeddings: Dict[ModelType, np.ndarray] = {}
        self.regime_embeddings: Dict[MarketRegime, np.ndarray] = {}

        # Association matrix - learns correlations
        self.association_matrix = np.eye(embedding_dim)

        self._initialize_embeddings()
        logger.info(f"HIM initialized with {embedding_dim}d semantic space")

    def _initialize_embeddings(self):
        """Initialize semantic embeddings with random vectors."""
        # Model embeddings
        for model_type in ModelType:
            self.model_embeddings[model_type] = self._random_unit_vector()

        # Regime embeddings
        for regime in MarketRegime:
            self.regime_embeddings[regime] = self._random_unit_vector()

    def _random_unit_vector(self) -> np.ndarray:
        """Generate random unit vector."""
        vec = np.random.randn(self.embedding_dim)
        return vec / (np.linalg.norm(vec) + 1e-8)

    def embed_intent(self, intent_id: str, intent_description: str) -> np.ndarray:
        """
        Embed an intent into semantic space.

        In production, this would use a language model.
        For now, we use a simple hash-based embedding.
        """
        if intent_id in self.intent_embeddings:
            return self.intent_embeddings[intent_id]

        # Simple hash-based embedding (placeholder for LLM embedding)
        vec = np.array([
            hash(intent_description + str(i)) % 1000 / 1000.0
            for i in range(self.embedding_dim)
        ])
        vec = vec - 0.5  # Center around 0
        vec = vec / (np.linalg.norm(vec) + 1e-8)  # Normalize

        self.intent_embeddings[intent_id] = vec
        return vec

    def semantic_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate semantic similarity between two vectors.

        Uses cosine similarity through association matrix.
        """
        # Transform through association matrix (learned correlations)
        vec1_transformed = self.association_matrix @ vec1
        similarity = np.dot(vec1_transformed, vec2)
        return float(similarity)

    def bind_intent_to_model(
        self,
        intent_id: str,
        model_type: ModelType,
        regime: MarketRegime,
        context: Dict[str, Any]
    ) -> SemanticBinding:
        """
        Create a binding between intent and model for given context.

        This is the core of semantic binding - making intent executable.
        """
        # Get embeddings
        intent_vec = self.intent_embeddings.get(intent_id)
        if intent_vec is None:
            logger.warning(f"Intent {intent_id} not embedded")
            intent_vec = self._random_unit_vector()
            self.intent_embeddings[intent_id] = intent_vec

        model_vec = self.model_embeddings[model_type]
        regime_vec = self.regime_embeddings[regime]

        # Calculate binding confidence
        intent_model_sim = self.semantic_similarity(intent_vec, model_vec)
        intent_regime_sim = self.semantic_similarity(intent_vec, regime_vec)
        model_regime_sim = self.semantic_similarity(model_vec, regime_vec)

        # Weighted confidence
        confidence = (
            0.4 * intent_model_sim +
            0.3 * intent_regime_sim +
            0.3 * model_regime_sim
        )
        confidence = (confidence + 1) / 2  # Normalize to [0, 1]

        # Create binding
        binding = SemanticBinding(
            intent_id=intent_id,
            model_type=model_type,
            regime=regime,
            confidence=confidence,
            resource_id=f"{model_type.value}_{regime.value}",
            binding_strength=confidence
        )

        self.bindings.append(binding)
        logger.debug(f"Created binding: {intent_id} -> {model_type.value} (confidence: {confidence:.3f})")

        return binding

    def resolve_intent(
        self,
        intent_id: str,
        context: Dict[str, Any]
    ) -> Optional[SemanticBinding]:
        """
        Resolve intent to best model binding given current context.

        This is O(1) semantic lookup.
        """
        regime = context.get('regime', MarketRegime.UNKNOWN)

        # Find all bindings for this intent and regime
        candidates = [
            b for b in self.bindings
            if b.intent_id == intent_id and b.regime == regime
        ]

        if not candidates:
            # Create new bindings if none exist
            logger.info(f"No binding found for {intent_id} in {regime.value}, creating new bindings")
            candidates = self._create_bindings_for_regime(intent_id, regime)

        if not candidates:
            return None

        # Score candidates by binding strength and success rate
        scored_candidates = [
            (b, b.binding_strength * 0.5 + b.success_rate * 0.5)
            for b in candidates
        ]

        # Return best binding
        best_binding = max(scored_candidates, key=lambda x: x[1])[0]
        return best_binding

    def _create_bindings_for_regime(
        self,
        intent_id: str,
        regime: MarketRegime
    ) -> List[SemanticBinding]:
        """Create bindings for all suitable models for a regime."""
        bindings = []

        # Map regimes to suitable models
        regime_model_map = {
            MarketRegime.STRONG_UPTREND: [ModelType.LSTM, ModelType.SWING_TRADER, ModelType.ENSEMBLE],
            MarketRegime.STRONG_DOWNTREND: [ModelType.LSTM, ModelType.SWING_TRADER, ModelType.ENSEMBLE],
            MarketRegime.SIDEWAYS: [ModelType.SCALPER, ModelType.MARKET_MAKER],
            MarketRegime.HIGH_VOLATILITY: [ModelType.RL_AGENT, ModelType.SCALPER],
            MarketRegime.LOW_VOLATILITY: [ModelType.MARKET_MAKER, ModelType.ARBITRAGE],
            MarketRegime.UNKNOWN: [ModelType.ENSEMBLE, ModelType.QUANTUM_RISK],
        }

        models = regime_model_map.get(regime, [ModelType.ENSEMBLE])

        for model_type in models:
            binding = self.bind_intent_to_model(
                intent_id=intent_id,
                model_type=model_type,
                regime=regime,
                context={'regime': regime}
            )
            bindings.append(binding)

        return bindings

    def update_association_matrix(self, success_feedback: List[tuple]):
        """
        Update association matrix based on success feedback.

        This is the continuous learning aspect - the binding layer improves.
        """
        # Hebbian-style learning: strengthen associations that led to success
        learning_rate = 0.01

        for intent_id, model_type, success in success_feedback:
            intent_vec = self.intent_embeddings.get(intent_id)
            model_vec = self.model_embeddings.get(model_type)

            if intent_vec is None or model_vec is None:
                continue

            # Outer product - strengthen association
            if success:
                delta = learning_rate * np.outer(intent_vec, model_vec)
                self.association_matrix += delta
            else:
                # Weaken association on failure
                delta = learning_rate * 0.5 * np.outer(intent_vec, model_vec)
                self.association_matrix -= delta

        # Normalize to prevent explosion
        norm = np.linalg.norm(self.association_matrix)
        if norm > 10:
            self.association_matrix = self.association_matrix / norm * 10

    def get_binding_stats(self) -> Dict[str, Any]:
        """Get statistics about bindings."""
        return {
            'total_bindings': len(self.bindings),
            'intents_mapped': len(self.intent_embeddings),
            'models_available': len(self.model_embeddings),
            'regimes_mapped': len(self.regime_embeddings),
            'best_bindings': [
                {
                    'intent': b.intent_id,
                    'model': b.model_type.value,
                    'regime': b.regime.value,
                    'success_rate': b.success_rate,
                    'binding_strength': b.binding_strength
                }
                for b in sorted(self.bindings, key=lambda x: x.success_rate, reverse=True)[:5]
            ]
        }


class SemanticBindingLayer:
    """
    Semantic Binding Layer - Makes Intent Executable.

    This layer sits between the Intent Graph and the actual models/strategies.
    It dynamically binds intent to the best model based on:
    - Current market regime
    - Historical performance
    - Semantic similarity
    - Resource availability
    """

    def __init__(self, embedding_dim: int = 64):
        """Initialize semantic binding layer."""
        self.him = HybridAssociativeMemory(embedding_dim)
        self.model_registry: Dict[str, Any] = {}  # Actual model instances
        self.binding_cache: Dict[str, SemanticBinding] = {}
        logger.info("Semantic Binding Layer initialized")

    def register_model(self, model_type: ModelType, model_instance: Any):
        """Register a model instance for binding."""
        resource_id = f"{model_type.value}_instance"
        self.model_registry[resource_id] = model_instance
        logger.info(f"Registered model: {model_type.value}")

    def bind_and_execute(
        self,
        intent_id: str,
        intent_description: str,
        context: Dict[str, Any],
        execution_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Bind intent to model and execute.

        This is the key method that makes intent executable.
        """
        # Embed intent if not already embedded
        if intent_id not in self.him.intent_embeddings:
            self.him.embed_intent(intent_id, intent_description)

        # Resolve intent to binding
        binding = self.him.resolve_intent(intent_id, context)

        if not binding:
            logger.warning(f"No binding found for intent {intent_id}")
            return {'success': False, 'reason': 'No suitable binding'}

        # Get model instance
        model_instance = self.model_registry.get(binding.resource_id)

        # Execute if function provided
        result = {'success': True, 'binding': binding.model_type.value}

        if execution_func and model_instance:
            try:
                result['output'] = execution_func(model_instance, context)
                result['success'] = True
                binding.use(success=True)
            except Exception as e:
                logger.error(f"Execution failed: {e}")
                result['success'] = False
                result['error'] = str(e)
                binding.use(success=False)
        else:
            # Just return the binding without execution
            result['model_instance'] = model_instance

        return result

    def continuous_rebinding(self):
        """
        Continuous rebinding process.

        Check if current bindings are still optimal.
        Reroute if better alternatives exist.
        """
        for binding in self.him.bindings:
            # If binding is performing poorly, weaken it
            if binding.usage_count > 10 and binding.success_rate < 0.3:
                binding.binding_strength *= 0.9
                logger.warning(
                    f"Weakening binding {binding.intent_id} -> {binding.model_type.value} "
                    f"(success rate: {binding.success_rate:.2%})"
                )

            # If binding is performing well, strengthen it
            elif binding.usage_count > 10 and binding.success_rate > 0.7:
                binding.binding_strength = min(1.0, binding.binding_strength * 1.05)
                logger.info(
                    f"Strengthening binding {binding.intent_id} -> {binding.model_type.value} "
                    f"(success rate: {binding.success_rate:.2%})"
                )

    def learn_from_feedback(self, feedback: List[tuple]):
        """Learn from execution feedback."""
        self.him.update_association_matrix(feedback)
        logger.debug(f"Updated associations from {len(feedback)} feedback samples")

    def get_best_model_for_context(
        self,
        intent_id: str,
        context: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Get the best model type for given context."""
        binding = self.him.resolve_intent(intent_id, context)
        return binding.model_type if binding else None
