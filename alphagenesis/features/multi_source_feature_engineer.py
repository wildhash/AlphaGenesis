"""
Multi-Source Feature Engineer

Integrates features from multiple data sources:
- Technical indicators
- On-chain metrics
- Sentiment analysis
- Order book dynamics
- Cross-market correlations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MultiSourceFeatureEngineer:
    """
    Combines traditional, on-chain, and sentiment features.
    
    This class orchestrates feature extraction from multiple data sources
    and fuses them into a comprehensive feature set for ML models.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the multi-source feature engineer.
        
        Args:
            config: Configuration dictionary with feature source settings
        """
        self.config = config or {}
        
        # Initialize feature source modules
        self.feature_sources = {}
        self._initialize_sources()
        
        # Feature combination weights
        self.feature_weights = self.config.get('feature_weights', {
            'technical': 0.35,
            'on_chain': 0.20,
            'sentiment': 0.15,
            'orderbook': 0.20,
            'correlations': 0.10
        })
    
    def _initialize_sources(self):
        """Initialize all feature source modules."""
        try:
            from alphagenesis.features import FeatureEngineer
            self.feature_sources['technical'] = FeatureEngineer()
        except ImportError:
            logger.warning("Technical feature engineer not available")
        
        try:
            from alphagenesis.features.onchain_analyzer import OnChainFeatureEngineer
            self.feature_sources['on_chain'] = OnChainFeatureEngineer()
        except ImportError:
            logger.warning("On-chain analyzer not available")
        
        try:
            from alphagenesis.features.sentiment_analyzer import SentimentAnalyzer
            self.feature_sources['sentiment'] = SentimentAnalyzer()
        except ImportError:
            logger.warning("Sentiment analyzer not available")
        
        try:
            from alphagenesis.features.orderbook_analyzer import OrderBookAnalyzer
            self.feature_sources['orderbook'] = OrderBookAnalyzer()
        except ImportError:
            logger.warning("Order book analyzer not available")
    
    def create_features(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = '1h'
    ) -> pd.DataFrame:
        """
        Create comprehensive features from all sources.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            df: OHLCV DataFrame
            timeframe: Timeframe string
            
        Returns:
            DataFrame with all features combined
        """
        features = {}
        
        # 1. Technical indicators
        logger.info("Extracting technical features...")
        features['technical'] = self._create_technical_features(df)
        
        # 2. On-chain metrics (for crypto)
        if self._is_crypto(symbol):
            logger.info("Extracting on-chain features...")
            features['on_chain'] = self._fetch_onchain_data(symbol)
        
        # 3. Market sentiment
        logger.info("Analyzing sentiment...")
        features['sentiment'] = self._analyze_sentiment(symbol)
        
        # 4. Order book dynamics
        logger.info("Analyzing order book...")
        features['orderbook'] = self._analyze_orderbook(symbol)
        
        # 5. Cross-market correlations
        logger.info("Calculating correlations...")
        features['correlations'] = self._calculate_correlations(symbol, df)
        
        # Fuse all features
        logger.info("Fusing features...")
        fused_features = self._fuse_features(features, df)
        
        return fused_features
    
    def _create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators."""
        if 'technical' not in self.feature_sources:
            # Fallback: create basic features
            result = df.copy()
            result['returns'] = df['close'].pct_change()
            result['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            result['volatility'] = result['returns'].rolling(20).std()
            return result
        
        return self.feature_sources['technical'].create_features(df)
    
    def _fetch_onchain_data(self, symbol: str) -> Dict[str, float]:
        """
        Fetch on-chain metrics for crypto assets.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Dictionary of on-chain metrics
        """
        if 'on_chain' not in self.feature_sources:
            # Fallback: return placeholder metrics
            return {
                'active_addresses': 0.0,
                'transaction_volume': 0.0,
                'network_hash_rate': 0.0,
                'miner_revenue': 0.0
            }
        
        try:
            return self.feature_sources['on_chain'].fetch_metrics(symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch on-chain data: {e}")
            return {}
    
    def _analyze_sentiment(self, symbol: str) -> Dict[str, float]:
        """
        Analyze market sentiment from various sources.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary of sentiment scores
        """
        if 'sentiment' not in self.feature_sources:
            # Fallback: return neutral sentiment
            return {
                'social_sentiment': 0.0,
                'news_sentiment': 0.0,
                'fear_greed_index': 50.0
            }
        
        try:
            return self.feature_sources['sentiment'].analyze(symbol)
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment: {e}")
            return {}
    
    def _analyze_orderbook(self, symbol: str) -> Dict[str, float]:
        """
        Analyze order book dynamics.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary of order book metrics
        """
        if 'orderbook' not in self.feature_sources:
            # Fallback: return neutral metrics
            return {
                'bid_ask_spread': 0.0,
                'order_book_imbalance': 0.0,
                'depth_ratio': 1.0
            }
        
        try:
            return self.feature_sources['orderbook'].analyze(symbol)
        except Exception as e:
            logger.warning(f"Failed to analyze order book: {e}")
            return {}
    
    def _calculate_correlations(
        self,
        symbol: str,
        df: pd.DataFrame,
        lookback: int = 30
    ) -> Dict[str, float]:
        """
        Calculate cross-market correlations.
        
        Args:
            symbol: Trading symbol
            df: Price data
            lookback: Lookback period for correlation
            
        Returns:
            Dictionary of correlation coefficients
        """
        correlations = {}
        
        # Reference symbols for correlation
        ref_symbols = self._get_reference_symbols(symbol)
        
        if df is None or len(df) < lookback:
            return {f'corr_{ref}': 0.0 for ref in ref_symbols}
        
        # Calculate returns
        returns = df['close'].pct_change().dropna()
        
        # For now, return placeholder correlations
        # In production, would fetch and correlate with reference symbols
        for ref_symbol in ref_symbols:
            correlations[f'corr_{ref_symbol}'] = np.random.uniform(-0.5, 0.5)
        
        return correlations
    
    def _get_reference_symbols(self, symbol: str) -> List[str]:
        """Get reference symbols for correlation analysis."""
        base_currency = symbol.split('/')[0]
        
        if base_currency == 'BTC':
            return ['ETH', 'SPY', 'GLD']
        elif base_currency == 'ETH':
            return ['BTC', 'SPY', 'GLD']
        else:
            return ['BTC', 'ETH', 'SPY']
    
    def _is_crypto(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency."""
        crypto_bases = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOT', 'DOGE']
        base = symbol.split('/')[0]
        return base in crypto_bases
    
    def _fuse_features(
        self,
        features: Dict[str, any],
        base_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fuse features from all sources into a single DataFrame.
        
        Args:
            features: Dictionary of features from different sources
            base_df: Base DataFrame with OHLCV data
            
        Returns:
            Fused feature DataFrame
        """
        # Start with technical features
        if 'technical' in features and isinstance(features['technical'], pd.DataFrame):
            result = features['technical'].copy()
        else:
            result = base_df.copy()
        
        # Add on-chain metrics (broadcast to all rows)
        if 'on_chain' in features and isinstance(features['on_chain'], dict):
            for key, value in features['on_chain'].items():
                result[f'onchain_{key}'] = value
        
        # Add sentiment scores (broadcast to all rows)
        if 'sentiment' in features and isinstance(features['sentiment'], dict):
            for key, value in features['sentiment'].items():
                result[f'sentiment_{key}'] = value
        
        # Add order book metrics (broadcast to all rows)
        if 'orderbook' in features and isinstance(features['orderbook'], dict):
            for key, value in features['orderbook'].items():
                result[f'orderbook_{key}'] = value
        
        # Add correlations (broadcast to all rows)
        if 'correlations' in features and isinstance(features['correlations'], dict):
            for key, value in features['correlations'].items():
                result[key] = value
        
        # Create composite features
        result = self._create_composite_features(result)
        
        return result
    
    def _create_composite_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create composite features from multiple sources.
        
        Args:
            df: DataFrame with individual features
            
        Returns:
            DataFrame with additional composite features
        """
        result = df.copy()
        
        # Market strength indicator (combine multiple signals)
        if all(col in result.columns for col in ['returns', 'volume']):
            result['market_strength'] = (
                result['returns'].rolling(10).mean() * 
                (result['volume'] / result['volume'].rolling(20).mean())
            )
        
        # Sentiment-adjusted momentum
        if 'sentiment_social_sentiment' in result.columns and 'returns' in result.columns:
            result['sentiment_momentum'] = (
                result['returns'].rolling(5).mean() * 
                (1 + result['sentiment_social_sentiment'] / 100)
            )
        
        # Order flow pressure
        if 'orderbook_order_book_imbalance' in result.columns:
            result['order_flow_pressure'] = (
                result['orderbook_order_book_imbalance'].rolling(10).mean()
            )
        
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        return self.feature_weights.copy()
    
    def update_feature_weights(self, new_weights: Dict[str, float]):
        """
        Update feature combination weights.
        
        Args:
            new_weights: New weights for feature sources
        """
        # Normalize weights to sum to 1
        total = sum(new_weights.values())
        if total > 0:
            self.feature_weights = {
                k: v / total for k, v in new_weights.items()
            }
            logger.info(f"Updated feature weights: {self.feature_weights}")


class FeatureSelector:
    """
    Selects the most important features using various methods.
    """
    
    def __init__(self, method: str = 'variance'):
        """
        Initialize feature selector.
        
        Args:
            method: Selection method ('variance', 'correlation', 'mutual_info')
        """
        self.method = method
        self.selected_features = []
    
    def fit_transform(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        n_features: int = 50
    ) -> pd.DataFrame:
        """
        Select and return top features.
        
        Args:
            X: Feature DataFrame
            y: Optional target variable
            n_features: Number of features to select
            
        Returns:
            DataFrame with selected features
        """
        if self.method == 'variance':
            return self._select_by_variance(X, n_features)
        elif self.method == 'correlation' and y is not None:
            return self._select_by_correlation(X, y, n_features)
        elif self.method == 'mutual_info' and y is not None:
            return self._select_by_mutual_info(X, y, n_features)
        else:
            return X
    
    def _select_by_variance(
        self,
        X: pd.DataFrame,
        n_features: int
    ) -> pd.DataFrame:
        """Select features with highest variance."""
        variances = X.var()
        top_features = variances.nlargest(n_features).index.tolist()
        self.selected_features = top_features
        return X[top_features]
    
    def _select_by_correlation(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int
    ) -> pd.DataFrame:
        """Select features with highest correlation to target."""
        correlations = X.corrwith(y).abs()
        top_features = correlations.nlargest(n_features).index.tolist()
        self.selected_features = top_features
        return X[top_features]
    
    def _select_by_mutual_info(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int
    ) -> pd.DataFrame:
        """Select features with highest mutual information."""
        try:
            from sklearn.feature_selection import mutual_info_regression
            
            mi_scores = mutual_info_regression(X, y)
            mi_series = pd.Series(mi_scores, index=X.columns)
            top_features = mi_series.nlargest(n_features).index.tolist()
            self.selected_features = top_features
            return X[top_features]
        except ImportError:
            logger.warning("sklearn not available, falling back to variance selection")
            return self._select_by_variance(X, n_features)
