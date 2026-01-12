# Semantic Dataflow Machine (SDM) Trading System

## The New Computational Contract

This is not a traditional trading bot. This is a **Semantic Dataflow Machine** - a post-Von Neumann architecture where:

- **Intent replaces instructions**
- **Semantic binding replaces compilation**
- **Continuous resolution replaces execution**
- **Learning is embodied in the dataflow**

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    INTENT GRAPH                              │
│  Defines WHAT we want (goals, constraints, relationships)   │
│  - Grow capital aggressively                                │
│  - Protect capital from losses                              │
│  - Exploit high-confidence opportunities                    │
│  - Maintain liquidity                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ Pressure Gradients
                   ↓
┌─────────────────────────────────────────────────────────────┐
│             SEMANTIC BINDING LAYER (HIM)                     │
│  Resolves HOW (which models/strategies for which context)   │
│  - O(1) semantic lookup                                     │
│  - Dynamic model selection based on market regime           │
│  - Continuous rebinding based on performance                │
└──────────────────┬──────────────────────────────────────────┘
                   │ Bound Actions
                   ↓
┌─────────────────────────────────────────────────────────────┐
│           CONSTRAINT PROPAGATION                             │
│  Ensures SAFETY through potential fields                    │
│  - Constraints as forces, not if-statements                 │
│  - Actions are SHAPED by constraints, not blocked           │
│  - Gradient descent toward safer states                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ Shaped Actions
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                 ETHICS ENGINE                                │
│  Enforces PRINCIPLES with asymmetric penalties              │
│  - Never exceed 20x leverage (hard boundary)                │
│  - Never lose more than 25% (catastrophic violation)        │
│  - Ethics as first-class constraints                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ Ethical Actions
                   ↓
┌─────────────────────────────────────────────────────────────┐
│           CONTINUOUS LEARNING ENGINE                         │
│  Ensures ADAPTATION through feedback                        │
│  - Records performance of every action                      │
│  - Identifies what works and what doesn't                   │
│  - Rewrites intent graph edges                              │
│  - Updates model bindings                                   │
│  - Adapts constraints based on results                      │
└──────────────────┬──────────────────────────────────────────┘
                   │ Execution
                   ↓
                 MARKET
```

## Key Innovations

### 1. Intent Graph - The True "Program"

No `main()`. No entry point. No termination.

Just a living graph of intents with:
- **Nodes**: Goals (maximize returns, minimize risk, etc.)
- **Edges**: Relationships (dependency, tradeoff, inhibition, feedback)
- **Activation**: Continuous pressure propagation through the graph

Intents have states and evolve over time based on success/failure.

### 2. Semantic Binding via HIM (Hybrid Associative Memory)

Traditional: `Code → Compilation → Binary`

SDM: `Intent → Semantic Binding → Dynamic Model Selection`

HIM provides O(1) semantic lookup to bind abstract intent to concrete models based on:
- Current market regime
- Historical performance
- Semantic similarity
- Resource availability

### 3. Constraints as Potential Fields

NOT: `if leverage > 20: raise Error`

BUT: Repulsive field that pushes actions away from dangerous states

Actions are **shaped** by constraints through gradient forces, not blocked by if-statements.

### 4. Ethics as Asymmetric Penalties

Violating ethics is MUCH more costly than satisfying them.

Hard boundaries (20x leverage, 25% drawdown) have near-infinite repulsion.

### 5. Continuous Learning - The System Never Stops Adapting

Every action generates feedback:
- Success/failure
- P&L
- Fitness to intent

The system continuously:
- Strengthens what works
- Weakens what doesn't
- Rewrites its own structure
- Adapts constraints
- Updates model bindings

## Quick Start

### 1. Set up environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your WEEX API credentials
nano .env
```

Required environment variables:
```bash
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSPHRASE=your_passphrase_here
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300  # 5 minutes
```

### 2. Install dependencies

```bash
# Using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

### 3. Run locally

```bash
# Using Poetry
poetry run python scripts/start_sdm_trading.py

# Or directly
python scripts/start_sdm_trading.py
```

### 4. Deploy to GCP

```bash
# Make deployment script executable
chmod +x deploy/deploy_to_gcp.sh

# Deploy (will prompt for confirmation)
./deploy/deploy_to_gcp.sh
```

## WEEX Hackathon Compliance

✅ **20x Leverage Cap**: Hard boundary in ethics engine
✅ **10% Daily Drawdown Limit**: Circuit breaker + ethics engine
✅ **25% Total Drawdown Limit**: Hard boundary in ethics engine
✅ **Minimum 10 Trades**: SDM will trade when high-confidence opportunities arise
✅ **No Manual Trading**: Fully autonomous AI system
✅ **API-Only Trading**: All execution via WEEX API
✅ **Genuine AI**: Multi-model system with continuous learning

## Competition Timeline

- **Preliminary Round (Early Bird)**: Jan 12, 8:00 PM – Feb 2, 11:59 PM (UTC+8)
- **Goal**: Top 2 in BUIDL group by final account balance
- **Starting Capital**: 1,000 USDT (competition funds)

## Monitoring

### View live logs
```bash
# If deployed via systemd
ssh alphagenesis@34.133.16.230 'sudo journalctl -u sdm-trading.service -f'

# If running locally
tail -f logs/sdm_trading_*.log
```

### Check performance
```bash
# On GCP
ssh alphagenesis@34.133.16.230
cd /home/alphagenesis/AlphaGenesis
ls -lh reports/sdm/
cat reports/sdm/learning_*.json | jq '.strategy_performance'
```

### View intent graph state
```python
from alphagenesis.sdm import IntentGraph

graph = IntentGraph()
graph.initialize_trading_intents()
print(graph.get_state_summary())
```

## System Components

### Core SDM Modules

- `alphagenesis/sdm/intent_graph.py` - Intent graph with activation propagation
- `alphagenesis/sdm/semantic_binding.py` - HIM and semantic binding layer
- `alphagenesis/sdm/continuous_learning.py` - Learning and adaptation engine
- `alphagenesis/sdm/constraint_propagation.py` - Constraint fields and forces
- `alphagenesis/sdm/ethics_engine.py` - Ethical constraints with asymmetric penalties
- `alphagenesis/sdm/sdm_engine.py` - Main SDM trading engine

### Integration with AlphaGenesis

The SDM system integrates with existing AlphaGenesis components:
- WEEX API client for execution
- Feature engineering for market analysis
- ML models (LSTM, Transformer, RL) via semantic binding
- Risk management and circuit breakers
- Performance tracking and reporting

## The Human-Machine Contract

> **Humans own purpose.**
> **Machines own process.**
> **Alignment lives in the binding layer.**

Humans do three things:
1. Declare intent (goals and constraints)
2. Set boundaries (ethical limits)
3. Approve stakes (capital at risk)

Machines do:
- Decomposition (intent → actions)
- Execution (market orders)
- Optimization (continuous improvement)
- Self-correction (adaptation)

If a human micromanages execution: **the system is failing**.

## Why This Is Inevitable

Because:
- Instruction density cannot scale with complexity
- Human-written code collapses under real-world entropy
- LLMs already proved intent → structure works

SDM just removes the illusion layer.

## Technical Details

### Intent Structure

```python
Intent = {
    goal: str,                      # What we want
    goal_type: IntentType,          # Category
    constraints: List[Constraint],  # Hard/soft limits
    stakes: Stake,                  # What's at risk
    context: Dict,                  # Current context
    confidence_threshold: float,    # Min confidence to act
    priority: float                 # Relative importance
}
```

### Semantic Binding Process

1. Intent arrives in graph
2. Graph propagates activation
3. Most active intents are selected
4. For each intent + market context:
   - Query HIM for best model binding
   - Generate proposed action
   - Evaluate against all intents
   - Apply constraint propagation (shape action)
   - Apply ethical pressure
   - Execute if permitted

### Learning Cycle

1. Action executed → feedback recorded
2. Performance tracked per (intent, model, regime)
3. When performance drops below threshold:
   - Identify best/worst strategies
   - Boost successful intent priorities
   - Weaken failing intent priorities
   - Update HIM association matrix
   - Continuous rebinding of models
   - Adapt constraints based on P&L

## Troubleshooting

### "No binding found for intent"
- The system is creating new bindings dynamically
- Wait for a few iterations for bindings to establish

### "Circuit breaker tripped"
- Daily or total drawdown limit exceeded
- System is protecting capital - will resume after cooldown

### "Ethical violation: max_leverage"
- Proposed action would exceed 20x leverage
- Ethics engine blocked it (working as designed)

### Low trade frequency
- SDM is disciplined - only trades high-confidence opportunities
- This is by design (inspired by DeepSeek's winning strategy)

## Contributing

The SDM is designed to be extensible:

1. **Add new intents**: Modify `intent_graph.py` → `initialize_trading_intents()`
2. **Add new models**: Register in `semantic_binding.py` → `SemanticBindingLayer`
3. **Add new constraints**: Extend `constraint_propagation.py` → `initialize_trading_constraints()`
4. **Add new ethics**: Extend `ethics_engine.py` → `initialize_trading_ethics()`

## References

- [WEEX AI Wars Competition](https://www.weex.com/events/ai-trading)
- [WEEX API Documentation](https://www.weex.com/api-doc/ai/introduction)
- [Intent-Driven Computing Paper](#) (theoretical foundation)

## License

MIT License - See LICENSE file

---

**Built for WEEX AI Wars: Alpha Awakens**

*A new computational contract between humans and machines.*
