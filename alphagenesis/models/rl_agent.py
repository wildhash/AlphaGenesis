"""
Reinforcement Learning Trading Agent

Implements RL-based trading agents using various algorithms
(DQN, PPO, A2C) for automated trading strategies.
"""

import numpy as np
import gym
from gym import spaces
from typing import Dict, Any, Optional, Tuple
from loguru import logger

try:
    from stable_baselines3 import PPO, A2C, DQN
    from stable_baselines3.common.vec_env import DummyVecEnv
except ImportError:
    logger.warning("stable-baselines3 not installed. RL functionality will be limited.")


class TradingEnvironment(gym.Env):
    """
    Custom trading environment for reinforcement learning.
    
    Implements OpenAI Gym interface for training RL agents on trading tasks.
    
    Actions:
        0: Hold
        1: Buy
        2: Sell
    
    Observation Space:
        Market features (prices, indicators, portfolio state)
    
    Reward:
        Based on portfolio returns and risk-adjusted metrics
    """
    
    metadata = {"render.modes": ["human"]}
    
    def __init__(
        self,
        df: Any,
        initial_balance: float = 10000.0,
        transaction_fee: float = 0.001,
        lookback_window: int = 20,
    ):
        """
        Initialize trading environment.
        
        Args:
            df: DataFrame with market data and features
            initial_balance: Initial account balance
            transaction_fee: Transaction fee rate
            lookback_window: Number of historical steps to include in observation
        """
        super(TradingEnvironment, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.lookback_window = lookback_window
        
        # Define action and observation spaces
        self.action_space = spaces.Discrete(3)  # Hold, Buy, Sell
        
        # Observation includes: price features + portfolio state
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(lookback_window * len(df.columns) + 3,),
            dtype=np.float32,
        )
        
        self.reset()
    
    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        self.current_step = self.lookback_window
        self.balance = self.initial_balance
        self.shares_held = 0.0
        self.total_value = self.initial_balance
        self.trades = []
        
        return self._get_observation()
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation.
        
        Returns:
            Observation array
        """
        # Get historical window of market features
        start = max(0, self.current_step - self.lookback_window)
        end = self.current_step
        
        market_data = self.df.iloc[start:end].values.flatten()
        
        # Add portfolio state
        current_price = self.df.iloc[self.current_step]["close"]
        portfolio_value = self.balance + self.shares_held * current_price
        
        portfolio_state = np.array([
            self.balance / self.initial_balance,
            self.shares_held * current_price / self.initial_balance,
            portfolio_value / self.initial_balance,
        ])
        
        observation = np.concatenate([market_data, portfolio_state])
        return observation.astype(np.float32)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (0=Hold, 1=Buy, 2=Sell)
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        current_price = self.df.iloc[self.current_step]["close"]
        prev_value = self.balance + self.shares_held * current_price
        
        # Execute action
        if action == 1:  # Buy
            shares_to_buy = self.balance / current_price
            cost = shares_to_buy * current_price * (1 + self.transaction_fee)
            if cost <= self.balance:
                self.shares_held += shares_to_buy
                self.balance -= cost
                self.trades.append(("buy", current_price, shares_to_buy))
        
        elif action == 2:  # Sell
            if self.shares_held > 0:
                proceeds = self.shares_held * current_price * (1 - self.transaction_fee)
                self.balance += proceeds
                self.trades.append(("sell", current_price, self.shares_held))
                self.shares_held = 0.0
        
        # Move to next step
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        
        # Calculate reward
        new_value = self.balance + self.shares_held * current_price
        reward = (new_value - prev_value) / prev_value
        
        # Get next observation
        observation = self._get_observation() if not done else np.zeros(self.observation_space.shape)
        
        info = {
            "balance": self.balance,
            "shares_held": self.shares_held,
            "total_value": new_value,
            "trades": len(self.trades),
        }
        
        return observation, reward, done, info
    
    def render(self, mode: str = "human") -> None:
        """
        Render environment state.
        
        Args:
            mode: Render mode
        """
        current_price = self.df.iloc[self.current_step]["close"]
        portfolio_value = self.balance + self.shares_held * current_price
        profit = portfolio_value - self.initial_balance
        profit_pct = (profit / self.initial_balance) * 100
        
        print(f"Step: {self.current_step}")
        print(f"Price: {current_price:.2f}")
        print(f"Balance: {self.balance:.2f}")
        print(f"Shares: {self.shares_held:.4f}")
        print(f"Portfolio Value: {portfolio_value:.2f}")
        print(f"Profit: {profit:.2f} ({profit_pct:.2f}%)")
        print(f"Total Trades: {len(self.trades)}")
        print("-" * 50)


class RLTradingAgent:
    """
    Reinforcement Learning agent for trading.
    
    Wraps various RL algorithms (PPO, A2C, DQN) and provides a unified
    interface for training and prediction.
    """
    
    def __init__(
        self,
        algorithm: str = "PPO",
        env: Optional[TradingEnvironment] = None,
        **kwargs,
    ):
        """
        Initialize RL trading agent.
        
        Args:
            algorithm: RL algorithm to use ('PPO', 'A2C', 'DQN')
            env: Trading environment
            **kwargs: Additional arguments for the algorithm
        """
        self.algorithm = algorithm
        self.env = env
        self.model = None
        
        if env is not None:
            self._initialize_model(**kwargs)
    
    def _initialize_model(self, **kwargs):
        """Initialize RL model based on selected algorithm."""
        env = DummyVecEnv([lambda: self.env])
        
        if self.algorithm == "PPO":
            self.model = PPO("MlpPolicy", env, verbose=1, **kwargs)
        elif self.algorithm == "A2C":
            self.model = A2C("MlpPolicy", env, verbose=1, **kwargs)
        elif self.algorithm == "DQN":
            self.model = DQN("MlpPolicy", env, verbose=1, **kwargs)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
        
        logger.info(f"Initialized {self.algorithm} agent")
    
    def train(self, total_timesteps: int = 10000) -> None:
        """
        Train the RL agent.
        
        Args:
            total_timesteps: Total training timesteps
        """
        if self.model is None:
            raise ValueError("Model not initialized. Provide an environment first.")
        
        logger.info(f"Training {self.algorithm} agent for {total_timesteps} timesteps")
        self.model.learn(total_timesteps=total_timesteps)
        logger.info("Training completed")
    
    def predict(self, observation: np.ndarray) -> int:
        """
        Predict action for given observation.
        
        Args:
            observation: Current observation
            
        Returns:
            Action to take
        """
        if self.model is None:
            raise ValueError("Model not initialized or trained")
        
        action, _ = self.model.predict(observation, deterministic=True)
        return int(action)
    
    def save(self, path: str) -> None:
        """
        Save model to disk.
        
        Args:
            path: Path to save model
        """
        if self.model is not None:
            self.model.save(path)
            logger.info(f"Model saved to {path}")
    
    def load(self, path: str) -> None:
        """
        Load model from disk.
        
        Args:
            path: Path to load model from
        """
        if self.algorithm == "PPO":
            self.model = PPO.load(path)
        elif self.algorithm == "A2C":
            self.model = A2C.load(path)
        elif self.algorithm == "DQN":
            self.model = DQN.load(path)
        
        logger.info(f"Model loaded from {path}")
