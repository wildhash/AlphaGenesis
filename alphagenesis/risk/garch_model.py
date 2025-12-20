"""
GARCH Model for Volatility Forecasting

Implements GARCH (Generalized Autoregressive Conditional Heteroskedasticity)
models for volatility estimation and forecasting.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
from loguru import logger

try:
    from arch import arch_model
    ARCH_AVAILABLE = True
except ImportError:
    ARCH_AVAILABLE = False
    logger.warning("arch package not installed. GARCH functionality will be limited.")


class GARCHModel:
    """
    GARCH model for volatility forecasting.
    
    Implements GARCH(p, q) models for modeling and forecasting
    time-varying volatility in financial returns.
    
    Attributes:
        p: Order of GARCH terms
        q: Order of ARCH terms
        model: Fitted GARCH model
    """
    
    def __init__(self, p: int = 1, q: int = 1, mean: str = "Zero"):
        """
        Initialize GARCH model.
        
        Args:
            p: Order of GARCH terms
            q: Order of ARCH terms
            mean: Mean model specification ('Zero', 'Constant', 'AR')
        """
        if not ARCH_AVAILABLE:
            raise ImportError("arch package is required for GARCH modeling")
        
        self.p = p
        self.q = q
        self.mean = mean
        self.model = None
        self.fitted_model = None
    
    def fit(self, returns: pd.Series, update_freq: int = 0) -> None:
        """
        Fit GARCH model to returns data.
        
        Args:
            returns: Returns series
            update_freq: Frequency of progress updates (0 for no updates)
        """
        # Remove NaN values
        returns = returns.dropna()
        
        if len(returns) < 50:
            logger.warning("Insufficient data for GARCH fitting (minimum 50 observations)")
            return
        
        try:
            # Multiply by 100 to avoid numerical issues with small values
            scaled_returns = returns * 100
            
            # Create and fit GARCH model
            self.model = arch_model(
                scaled_returns,
                vol="Garch",
                p=self.p,
                q=self.q,
                mean=self.mean,
            )
            
            self.fitted_model = self.model.fit(update_freq=update_freq, disp="off")
            
            logger.info(
                f"GARCH({self.p},{self.q}) model fitted successfully. "
                f"AIC: {self.fitted_model.aic:.2f}"
            )
            
        except Exception as e:
            logger.error(f"GARCH model fitting failed: {e}")
            raise
    
    def forecast_volatility(
        self,
        horizon: int = 1,
        method: str = "analytic",
    ) -> pd.DataFrame:
        """
        Forecast future volatility.
        
        Args:
            horizon: Forecast horizon (number of periods)
            method: Forecasting method ('analytic', 'simulation', 'bootstrap')
            
        Returns:
            DataFrame with volatility forecasts
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")
        
        try:
            forecasts = self.fitted_model.forecast(horizon=horizon, method=method)
            
            # Extract variance forecasts and convert back to original scale
            variance_forecast = forecasts.variance.values[-1, :] / 10000
            volatility_forecast = np.sqrt(variance_forecast)
            
            forecast_df = pd.DataFrame({
                "horizon": range(1, horizon + 1),
                "volatility": volatility_forecast,
                "variance": variance_forecast,
            })
            
            logger.debug(f"Generated {horizon}-step ahead volatility forecast")
            return forecast_df
            
        except Exception as e:
            logger.error(f"Volatility forecasting failed: {e}")
            raise
    
    def get_conditional_volatility(self) -> pd.Series:
        """
        Get conditional volatility from fitted model.
        
        Returns:
            Series of conditional volatility values
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")
        
        # Convert back to original scale
        conditional_vol = self.fitted_model.conditional_volatility / 100
        return conditional_vol
    
    def get_standardized_residuals(self) -> pd.Series:
        """
        Get standardized residuals from fitted model.
        
        Returns:
            Series of standardized residuals
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")
        
        return self.fitted_model.std_resid
    
    def calculate_var(
        self,
        confidence_level: float = 0.95,
        horizon: int = 1,
    ) -> float:
        """
        Calculate VaR using GARCH volatility forecast.
        
        Args:
            confidence_level: Confidence level for VaR
            horizon: Forecast horizon
            
        Returns:
            VaR estimate
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")
        
        from scipy import stats
        
        # Get volatility forecast
        vol_forecast = self.forecast_volatility(horizon=horizon)
        volatility = vol_forecast.iloc[-1]["volatility"]
        
        # Calculate VaR assuming normal distribution
        z_score = stats.norm.ppf(1 - confidence_level)
        var = -z_score * volatility * np.sqrt(horizon)
        
        logger.debug(f"GARCH-based VaR ({confidence_level*100}%): {var:.6f}")
        return var
    
    def summary(self) -> str:
        """
        Get model summary.
        
        Returns:
            Model summary string
        """
        if self.fitted_model is None:
            return "Model not fitted"
        
        return str(self.fitted_model.summary())
    
    @staticmethod
    def select_best_order(
        returns: pd.Series,
        max_p: int = 3,
        max_q: int = 3,
    ) -> Tuple[int, int]:
        """
        Select best GARCH order using AIC criterion.
        
        Args:
            returns: Returns series
            max_p: Maximum p order to test
            max_q: Maximum q order to test
            
        Returns:
            Tuple of (best_p, best_q)
        """
        if not ARCH_AVAILABLE:
            raise ImportError("arch package is required for GARCH modeling")
        
        best_aic = np.inf
        best_order = (1, 1)
        
        scaled_returns = returns.dropna() * 100
        
        for p in range(1, max_p + 1):
            for q in range(1, max_q + 1):
                try:
                    model = arch_model(scaled_returns, vol="Garch", p=p, q=q)
                    fitted = model.fit(disp="off")
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, q)
                        
                except Exception:
                    continue
        
        logger.info(f"Best GARCH order: ({best_order[0]}, {best_order[1]}) with AIC: {best_aic:.2f}")
        return best_order
