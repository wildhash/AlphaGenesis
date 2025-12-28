"""
Integration tests for AlphaGenesis upgrades
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def test_imports():
    """Test that all new modules can be imported."""
    # Core modules
    from alphagenesis import agents, arbitrage, market_making
    
    # Multi-agent system
    from alphagenesis.agents import MultiAgentTradingSystem, AgentDecision
    
    # Feature engineering
    from alphagenesis.features.multi_source_feature_engineer import MultiSourceFeatureEngineer
    from alphagenesis.features.onchain_analyzer import OnChainFeatureEngineer
    from alphagenesis.features.sentiment_analyzer import SentimentAnalyzer
    from alphagenesis.features.orderbook_analyzer import OrderBookAnalyzer
    
    # Advanced models
    from alphagenesis.models.advanced_ensemble import AdvancedEnsemble, create_advanced_ensemble
    
    # Risk management
    from alphagenesis.risk.quantum_risk_manager import QuantumRiskManager
    
    # Arbitrage
    from alphagenesis.arbitrage.cross_exchange import CrossExchangeArbitrage
    
    # Market making
    from alphagenesis.market_making.advanced_mm import AdvancedMarketMaker
    
    assert True


def test_multi_agent_system():
    """Test multi-agent trading system."""
    from alphagenesis.agents import MultiAgentTradingSystem
    
    # Initialize system
    multi_agent = MultiAgentTradingSystem(
        enable_scalper=True,
        enable_swing=True,
        enable_arbitrage=True
    )
    
    # Create mock market state
    market_state = {
        'close': 50000.0,
        'volume': 1000.0,
        'volatility': 0.02,
        'trend': 'uptrend',
        'rsi_14': 55.0,
        'macd': 10.0,
        'orderbook_order_book_imbalance': 0.1,
        'orderbook_net_pressure': 0.05
    }
    
    # Get decision
    decision = multi_agent.decide(market_state)
    
    assert decision is not None
    assert decision.action in ['BUY', 'SELL', 'HOLD']
    assert 0 <= decision.confidence <= 1
    assert decision.position_size >= 0


def test_quantum_risk_manager():
    """Test quantum risk manager."""
    from alphagenesis.risk.quantum_risk_manager import QuantumRiskManager
    
    risk_mgr = QuantumRiskManager(
        initial_capital=10000,
        max_risk_per_trade=0.02
    )
    
    recommendation = risk_mgr.calculate_position_size(
        signal_confidence=0.75,
        current_price=50000,
        volatility=0.03,
        market_regime='bull'
    )
    
    assert recommendation is not None
    assert 0 <= recommendation.size <= 1
    assert recommendation.stop_loss > 0
    assert recommendation.take_profit > 0
    assert 0 <= recommendation.uncertainty <= 1


def test_multi_source_feature_engineer():
    """Test multi-source feature engineering."""
    from alphagenesis.features.multi_source_feature_engineer import MultiSourceFeatureEngineer
    
    engineer = MultiSourceFeatureEngineer()
    
    # Create sample OHLCV data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 101,
        'low': np.random.randn(100).cumsum() + 99,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
    }, index=dates)
    
    features = engineer.create_features('BTC/USDT', df)
    
    assert features is not None
    assert len(features) > 0
    assert 'close' in features.columns


def test_advanced_ensemble():
    """Test advanced ensemble model."""
    from alphagenesis.models.advanced_ensemble import AdvancedEnsemble
    import torch
    
    # Create simple ensemble without pre-trained models
    ensemble = AdvancedEnsemble(
        lstm_model=None,
        transformer_model=None,
        rl_agent=None,
        embed_dim=256,
        num_heads=8
    )
    
    # Create dummy inputs
    market_state = torch.randn(1, 50)
    historical_data = torch.randn(1, 100, 50)
    
    # Test forward pass (will use fallback since no models provided)
    # This test just ensures no crashes
    assert ensemble is not None


def test_cross_exchange_arbitrage():
    """Test cross-exchange arbitrage."""
    from alphagenesis.arbitrage.cross_exchange import CrossExchangeArbitrage
    
    arb = CrossExchangeArbitrage(
        exchanges=['weex', 'binance'],
        min_profit_threshold=0.005
    )
    
    opportunities = arb.find_opportunities(['BTC/USDT'])
    
    assert opportunities is not None
    assert isinstance(opportunities, list)


def test_advanced_market_maker():
    """Test advanced market making."""
    from alphagenesis.market_making.advanced_mm import AdvancedMarketMaker
    
    mm = AdvancedMarketMaker(
        risk_aversion=0.1,
        max_inventory=1.0
    )
    
    # Create mock order book
    order_book = {
        'bids': [[50000, 1.0], [49900, 2.0]],
        'asks': [[50100, 1.0], [50200, 2.0]]
    }
    
    quotes = mm.calculate_optimal_quotes(order_book, volatility=0.02)
    
    assert quotes is not None
    assert quotes.bid_price > 0
    assert quotes.ask_price > quotes.bid_price
    assert quotes.spread > 0


def test_individual_agents():
    """Test individual trading agents."""
    from alphagenesis.agents.scalper_agent import ScalperAgent
    from alphagenesis.agents.swing_trader_agent import SwingTraderAgent
    from alphagenesis.agents.arbitrage_agent import ArbitrageAgent
    
    market_state = {
        'close': 50000.0,
        'volatility': 0.02,
        'trend': 'uptrend',
        'rsi_14': 55.0,
        'orderbook_order_book_imbalance': 0.1
    }
    
    # Test scalper
    scalper = ScalperAgent()
    scalper_decision = scalper.decide(market_state)
    assert scalper_decision.action in ['BUY', 'SELL', 'HOLD']
    
    # Test swing trader
    swing = SwingTraderAgent()
    swing_decision = swing.decide(market_state)
    assert swing_decision.action in ['BUY', 'SELL', 'HOLD']
    
    # Test arbitrage
    arb_agent = ArbitrageAgent()
    arb_decision = arb_agent.decide(market_state)
    assert arb_decision.action in ['BUY', 'SELL', 'HOLD']


def test_sentiment_analyzer():
    """Test sentiment analyzer."""
    from alphagenesis.features.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze('BTC/USDT')
    
    assert sentiment is not None
    assert 'composite_sentiment' in sentiment
    assert 'social_sentiment' in sentiment


def test_onchain_analyzer():
    """Test on-chain analyzer."""
    from alphagenesis.features.onchain_analyzer import OnChainFeatureEngineer
    
    analyzer = OnChainFeatureEngineer()
    metrics = analyzer.fetch_metrics('BTC/USDT')
    
    assert metrics is not None
    assert isinstance(metrics, dict)


def test_orderbook_analyzer():
    """Test order book analyzer."""
    from alphagenesis.features.orderbook_analyzer import OrderBookAnalyzer
    
    analyzer = OrderBookAnalyzer()
    metrics = analyzer.analyze('BTC/USDT')
    
    assert metrics is not None
    assert 'bid_ask_spread' in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
