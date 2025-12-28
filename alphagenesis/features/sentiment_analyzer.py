"""
Sentiment Analyzer

Analyzes market sentiment from multiple sources:
- Social media sentiment (Twitter, Reddit, etc.)
- News sentiment
- Fear & Greed Index
- Market positioning data
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzes market sentiment from various sources.
    
    Aggregates sentiment data to provide trading signals based on
    market psychology and crowd behavior.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize sentiment analyzer.
        
        Args:
            api_keys: Dictionary of API keys for different services
        """
        self.api_keys = api_keys or {}
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes cache
        
    def analyze(self, symbol: str) -> Dict[str, float]:
        """
        Analyze sentiment for a trading symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dictionary of sentiment scores
        """
        base_currency = symbol.split('/')[0]
        
        # Check cache
        cache_key = f"{base_currency}_sentiment"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_data
        
        sentiment_scores = {}
        
        try:
            # Social media sentiment
            sentiment_scores.update(self._analyze_social_media(base_currency))
            
            # News sentiment
            sentiment_scores.update(self._analyze_news(base_currency))
            
            # Fear & Greed Index
            sentiment_scores.update(self._fetch_fear_greed_index(base_currency))
            
            # Aggregated sentiment score
            sentiment_scores['composite_sentiment'] = self._calculate_composite_sentiment(
                sentiment_scores
            )
            
            # Cache results
            self.cache[cache_key] = (datetime.now(), sentiment_scores)
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            sentiment_scores = self._get_default_sentiment()
        
        return sentiment_scores
    
    def _analyze_social_media(self, currency: str) -> Dict[str, float]:
        """
        Analyze sentiment from social media.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary of social media sentiment scores
        """
        # Placeholder implementation
        # In production, would integrate with Twitter API, Reddit API, etc.
        
        # Simulate sentiment scores between -100 and +100
        twitter_sentiment = np.random.uniform(-50, 50)
        reddit_sentiment = np.random.uniform(-50, 50)
        
        # Simulate engagement metrics
        twitter_volume = np.random.uniform(1000, 10000)
        reddit_volume = np.random.uniform(100, 1000)
        
        # Calculate weighted sentiment
        total_volume = twitter_volume + reddit_volume
        weighted_sentiment = (
            (twitter_sentiment * twitter_volume + reddit_sentiment * reddit_volume) 
            / total_volume
        )
        
        return {
            'social_sentiment': weighted_sentiment,
            'twitter_sentiment': twitter_sentiment,
            'reddit_sentiment': reddit_sentiment,
            'social_volume': total_volume,
            'social_volume_change': np.random.uniform(-0.2, 0.2)
        }
    
    def _analyze_news(self, currency: str) -> Dict[str, float]:
        """
        Analyze sentiment from news articles.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary of news sentiment scores
        """
        # Placeholder implementation
        # In production, would use news APIs and NLP models
        
        return {
            'news_sentiment': np.random.uniform(-50, 50),
            'news_volume': np.random.uniform(10, 100),
            'positive_news_count': np.random.randint(0, 20),
            'negative_news_count': np.random.randint(0, 20),
            'news_momentum': np.random.uniform(-10, 10)
        }
    
    def _fetch_fear_greed_index(self, currency: str) -> Dict[str, float]:
        """
        Fetch crypto fear & greed index.
        
        Args:
            currency: Base currency
            
        Returns:
            Dictionary with fear & greed metrics
        """
        # Placeholder implementation
        # In production, would fetch from alternative.me or similar APIs
        
        fear_greed_value = np.random.uniform(20, 80)
        
        # Classify sentiment
        if fear_greed_value < 25:
            classification = "extreme_fear"
        elif fear_greed_value < 45:
            classification = "fear"
        elif fear_greed_value < 55:
            classification = "neutral"
        elif fear_greed_value < 75:
            classification = "greed"
        else:
            classification = "extreme_greed"
        
        return {
            'fear_greed_index': fear_greed_value,
            'fear_greed_classification': hash(classification) % 100,  # Numeric encoding
            'fear_greed_change': np.random.uniform(-5, 5)
        }
    
    def _calculate_composite_sentiment(
        self,
        sentiment_scores: Dict[str, float]
    ) -> float:
        """
        Calculate composite sentiment from all sources.
        
        Args:
            sentiment_scores: Dictionary of individual sentiment scores
            
        Returns:
            Composite sentiment score (-100 to +100)
        """
        # Weight different sources
        weights = {
            'social_sentiment': 0.40,
            'news_sentiment': 0.30,
            'fear_greed_index': 0.30
        }
        
        composite = 0.0
        total_weight = 0.0
        
        for key, weight in weights.items():
            if key in sentiment_scores:
                value = sentiment_scores[key]
                
                # Normalize fear_greed_index to -100 to +100 scale
                if key == 'fear_greed_index':
                    value = (value - 50) * 2
                
                composite += value * weight
                total_weight += weight
        
        if total_weight > 0:
            composite /= total_weight
        
        return composite
    
    def _get_default_sentiment(self) -> Dict[str, float]:
        """Return default sentiment when data is unavailable."""
        return {
            'social_sentiment': 0.0,
            'news_sentiment': 0.0,
            'fear_greed_index': 50.0,
            'composite_sentiment': 0.0
        }
    
    def detect_sentiment_extremes(
        self,
        sentiment_scores: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Detect extreme sentiment conditions.
        
        Args:
            sentiment_scores: Dictionary of sentiment scores
            
        Returns:
            Dictionary with extreme sentiment indicators
        """
        composite = sentiment_scores.get('composite_sentiment', 0)
        fear_greed = sentiment_scores.get('fear_greed_index', 50)
        
        # Extreme conditions (potential reversal signals)
        extreme_fear = composite < -60 or fear_greed < 20
        extreme_greed = composite > 60 or fear_greed > 80
        
        # Contrarian signals
        contrarian_buy = extreme_fear
        contrarian_sell = extreme_greed
        
        return {
            'extreme_fear': extreme_fear,
            'extreme_greed': extreme_greed,
            'contrarian_buy_signal': contrarian_buy,
            'contrarian_sell_signal': contrarian_sell,
            'sentiment_strength': abs(composite),
            'alert_level': 'high' if (extreme_fear or extreme_greed) else 'normal'
        }
    
    def calculate_sentiment_momentum(
        self,
        current_sentiment: float,
        historical_sentiment: List[float],
        window: int = 7
    ) -> Dict[str, float]:
        """
        Calculate sentiment momentum and trend.
        
        Args:
            current_sentiment: Current sentiment score
            historical_sentiment: List of historical sentiment scores
            window: Lookback window for momentum calculation
            
        Returns:
            Dictionary with sentiment momentum metrics
        """
        if len(historical_sentiment) < window:
            return {
                'sentiment_momentum': 0.0,
                'sentiment_acceleration': 0.0,
                'sentiment_trend': 'neutral'
            }
        
        recent_sentiment = historical_sentiment[-window:]
        avg_sentiment = np.mean(recent_sentiment)
        
        # Calculate momentum (rate of change)
        momentum = current_sentiment - avg_sentiment
        
        # Calculate acceleration (change in momentum)
        if len(historical_sentiment) >= window * 2:
            older_avg = np.mean(historical_sentiment[-window*2:-window])
            prev_momentum = avg_sentiment - older_avg
            acceleration = momentum - prev_momentum
        else:
            acceleration = 0.0
        
        # Determine trend
        if momentum > 5:
            trend = 'improving'
        elif momentum < -5:
            trend = 'deteriorating'
        else:
            trend = 'neutral'
        
        return {
            'sentiment_momentum': momentum,
            'sentiment_acceleration': acceleration,
            'sentiment_trend': hash(trend) % 100  # Numeric encoding
        }
    
    def get_sentiment_divergence(
        self,
        sentiment_scores: Dict[str, float],
        price_change: float
    ) -> Dict[str, any]:
        """
        Detect divergence between sentiment and price action.
        
        Args:
            sentiment_scores: Current sentiment scores
            price_change: Recent price change percentage
            
        Returns:
            Dictionary with divergence indicators
        """
        composite = sentiment_scores.get('composite_sentiment', 0)
        
        # Normalize to same scale
        sentiment_direction = np.sign(composite)
        price_direction = np.sign(price_change)
        
        # Detect divergence
        bullish_divergence = (price_direction < 0) and (sentiment_direction > 0)
        bearish_divergence = (price_direction > 0) and (sentiment_direction < 0)
        
        divergence_strength = abs(composite * price_change)
        
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence,
            'divergence_strength': divergence_strength,
            'sentiment_price_correlation': sentiment_direction * price_direction
        }


class SentimentStrategy:
    """
    Trading strategy based on sentiment analysis.
    """
    
    def __init__(self, analyzer: SentimentAnalyzer):
        """
        Initialize sentiment strategy.
        
        Args:
            analyzer: SentimentAnalyzer instance
        """
        self.analyzer = analyzer
        
    def generate_signal(
        self,
        symbol: str,
        price_change: float
    ) -> Dict[str, any]:
        """
        Generate trading signal based on sentiment.
        
        Args:
            symbol: Trading symbol
            price_change: Recent price change
            
        Returns:
            Dictionary with signal and reasoning
        """
        sentiment_scores = self.analyzer.analyze(symbol)
        extremes = self.analyzer.detect_sentiment_extremes(sentiment_scores)
        divergence = self.analyzer.get_sentiment_divergence(
            sentiment_scores, price_change
        )
        
        # Generate signal
        signal = 'HOLD'
        confidence = 0.5
        reasoning = []
        
        # Contrarian signals at extremes
        if extremes['contrarian_buy_signal']:
            signal = 'BUY'
            confidence = 0.7
            reasoning.append("Extreme fear detected - contrarian buy opportunity")
        elif extremes['contrarian_sell_signal']:
            signal = 'SELL'
            confidence = 0.7
            reasoning.append("Extreme greed detected - contrarian sell opportunity")
        
        # Divergence signals
        if divergence['bullish_divergence']:
            signal = 'BUY'
            confidence = 0.6
            reasoning.append("Bullish divergence: positive sentiment with price decline")
        elif divergence['bearish_divergence']:
            signal = 'SELL'
            confidence = 0.6
            reasoning.append("Bearish divergence: negative sentiment with price rise")
        
        # Momentum-based signals
        composite = sentiment_scores.get('composite_sentiment', 0)
        if abs(composite) > 30:
            if composite > 0:
                signal = 'BUY'
                confidence = min(0.8, abs(composite) / 100)
                reasoning.append(f"Strong positive sentiment: {composite:.1f}")
            else:
                signal = 'SELL'
                confidence = min(0.8, abs(composite) / 100)
                reasoning.append(f"Strong negative sentiment: {composite:.1f}")
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': ' | '.join(reasoning) if reasoning else 'Neutral sentiment',
            'sentiment_scores': sentiment_scores
        }
