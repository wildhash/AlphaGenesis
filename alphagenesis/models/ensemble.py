"""
Ensemble Model for Signal Blending

Meta-model that combines predictions from multiple models (LSTM, RL, Transformer)
to generate robust trading signals.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from loguru import logger
import torch
import torch.nn as nn


class EnsemblePredictor:
    """
    Ensemble model that blends signals from multiple ML models.
    
    Supports multiple aggregation strategies:
    - Simple averaging
    - Weighted averaging
    - Voting
    - Meta-learning (stacking)
    """
    
    def __init__(
        self,
        models: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None,
        aggregation_method: str = 'weighted_average',
    ):
        """
        Initialize EnsemblePredictor.
        
        Args:
            models: Dictionary of model_name -> model_instance
            weights: Dictionary of model_name -> weight (for weighted average)
            aggregation_method: 'simple_average', 'weighted_average', 'voting', 'stacking'
        """
        self.models = models or {}
        self.weights = weights or {}
        self.aggregation_method = aggregation_method
        
        # Normalize weights
        if self.weights:
            total_weight = sum(self.weights.values())
            self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        # For stacking meta-learner
        self.meta_learner = None
        
        logger.info(
            f"EnsemblePredictor initialized with {len(self.models)} models, "
            f"aggregation={aggregation_method}"
        )
    
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """
        Add a model to the ensemble.
        
        Args:
            name: Model name/identifier
            model: Model instance with predict() method
            weight: Weight for weighted averaging
        """
        self.models[name] = model
        self.weights[name] = weight
        
        # Re-normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        logger.info(f"Added model '{name}' with weight {weight:.3f}")
    
    def predict(
        self,
        X: np.ndarray,
        return_individual: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate ensemble prediction.
        
        Args:
            X: Input features
            return_individual: Whether to return individual model predictions
            
        Returns:
            Dictionary with ensemble prediction and optionally individual predictions
        """
        if not self.models:
            logger.error("No models in ensemble")
            return {'ensemble': None}
        
        # Collect predictions from all models
        predictions = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    pred = model.predict(X)
                elif hasattr(model, 'forward'):
                    # PyTorch model
                    with torch.no_grad():
                        if isinstance(X, np.ndarray):
                            X_tensor = torch.FloatTensor(X)
                        else:
                            X_tensor = X
                        pred = model.forward(X_tensor).numpy()
                else:
                    logger.warning(f"Model '{name}' has no predict method")
                    continue
                
                predictions[name] = pred
                logger.debug(f"Model '{name}' prediction: {pred}")
                
            except Exception as e:
                logger.error(f"Error getting prediction from model '{name}': {e}")
                continue
        
        if not predictions:
            logger.error("No successful predictions from any model")
            return {'ensemble': None}
        
        # Aggregate predictions
        if self.aggregation_method == 'simple_average':
            ensemble_pred = self._simple_average(predictions)
        elif self.aggregation_method == 'weighted_average':
            ensemble_pred = self._weighted_average(predictions)
        elif self.aggregation_method == 'voting':
            ensemble_pred = self._voting(predictions)
        elif self.aggregation_method == 'stacking':
            ensemble_pred = self._stacking(predictions, X)
        else:
            logger.warning(f"Unknown aggregation method: {self.aggregation_method}")
            ensemble_pred = self._simple_average(predictions)
        
        result = {'ensemble': ensemble_pred}
        
        if return_individual:
            result['individual'] = predictions
        
        logger.debug(f"Ensemble prediction: {ensemble_pred}")
        
        return result
    
    def _simple_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Simple average of all predictions.
        """
        pred_array = np.array(list(predictions.values()))
        return np.mean(pred_array, axis=0)
    
    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Weighted average based on model weights.
        """
        weighted_sum = None
        total_weight = 0.0
        
        for name, pred in predictions.items():
            weight = self.weights.get(name, 1.0)
            
            if weighted_sum is None:
                weighted_sum = pred * weight
            else:
                weighted_sum += pred * weight
            
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else weighted_sum
    
    def _voting(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Majority voting (for classification).
        
        Each model votes for a class, and the most voted class wins.
        """
        # Convert continuous predictions to classes (-1, 0, 1)
        votes = []
        
        for pred in predictions.values():
            # Threshold predictions
            vote = np.sign(pred)
            votes.append(vote)
        
        votes_array = np.array(votes)
        
        # Majority vote
        ensemble_vote = np.sign(np.sum(votes_array, axis=0))
        
        return ensemble_vote
    
    def _stacking(
        self,
        predictions: Dict[str, np.ndarray],
        X: np.ndarray,
    ) -> np.ndarray:
        """
        Stacking with meta-learner.
        
        Uses base model predictions as features for a meta-learner.
        """
        if self.meta_learner is None:
            logger.warning("Meta-learner not trained, falling back to weighted average")
            return self._weighted_average(predictions)
        
        # Combine predictions as features for meta-learner
        stacked_features = np.column_stack(list(predictions.values()))
        
        # Get meta-learner prediction
        try:
            meta_pred = self.meta_learner.predict(stacked_features)
            return meta_pred
        except Exception as e:
            logger.error(f"Error in meta-learner prediction: {e}")
            return self._weighted_average(predictions)
    
    def train_meta_learner(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        meta_learner_type: str = 'linear',
    ):
        """
        Train a meta-learner for stacking.
        
        Args:
            X_train: Training features
            y_train: Training labels
            meta_learner_type: Type of meta-learner ('linear', 'ridge', 'mlp')
        """
        # Get predictions from all base models
        base_predictions = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X_train)
                base_predictions[name] = pred
            except Exception as e:
                logger.error(f"Error getting training prediction from '{name}': {e}")
                continue
        
        if not base_predictions:
            logger.error("No base predictions for meta-learner training")
            return
        
        # Stack predictions as features
        stacked_features = np.column_stack(list(base_predictions.values()))
        
        # Train meta-learner
        if meta_learner_type == 'linear':
            from sklearn.linear_model import LinearRegression
            self.meta_learner = LinearRegression()
        elif meta_learner_type == 'ridge':
            from sklearn.linear_model import Ridge
            self.meta_learner = Ridge(alpha=1.0)
        elif meta_learner_type == 'mlp':
            from sklearn.neural_network import MLPRegressor
            self.meta_learner = MLPRegressor(hidden_layer_sizes=(50,), max_iter=1000)
        else:
            logger.error(f"Unknown meta-learner type: {meta_learner_type}")
            return
        
        self.meta_learner.fit(stacked_features, y_train)
        logger.info(f"Meta-learner trained with {meta_learner_type}")
    
    def calculate_model_performance(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> pd.DataFrame:
        """
        Calculate performance metrics for each model and the ensemble.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            DataFrame with performance metrics
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        results = []
        
        # Evaluate each model
        for name, model in self.models.items():
            try:
                pred = model.predict(X_test)
                
                mse = mean_squared_error(y_test, pred)
                mae = mean_absolute_error(y_test, pred)
                r2 = r2_score(y_test, pred)
                
                results.append({
                    'model': name,
                    'mse': mse,
                    'mae': mae,
                    'r2': r2,
                    'rmse': np.sqrt(mse),
                })
                
            except Exception as e:
                logger.error(f"Error evaluating model '{name}': {e}")
        
        # Evaluate ensemble
        try:
            ensemble_result = self.predict(X_test)
            ensemble_pred = ensemble_result['ensemble']
            
            mse = mean_squared_error(y_test, ensemble_pred)
            mae = mean_absolute_error(y_test, ensemble_pred)
            r2 = r2_score(y_test, ensemble_pred)
            
            results.append({
                'model': 'ensemble',
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'rmse': np.sqrt(mse),
            })
            
        except Exception as e:
            logger.error(f"Error evaluating ensemble: {e}")
        
        df = pd.DataFrame(results)
        logger.info(f"\nModel Performance:\n{df.to_string()}")
        
        return df
    
    def optimize_weights(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        method: str = 'grid_search',
    ) -> Dict[str, float]:
        """
        Optimize ensemble weights using validation data.
        
        Args:
            X_val: Validation features
            y_val: Validation labels
            method: Optimization method ('grid_search', 'minimize')
            
        Returns:
            Optimized weights dictionary
        """
        from sklearn.metrics import mean_squared_error
        from itertools import product
        
        model_names = list(self.models.keys())
        best_weights = None
        best_score = float('inf')
        
        if method == 'grid_search':
            # Grid search over weight combinations
            weight_options = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            
            for weights_tuple in product(weight_options, repeat=len(model_names)):
                if sum(weights_tuple) == 0:
                    continue
                
                # Normalize weights
                total = sum(weights_tuple)
                weights_dict = {
                    name: w / total
                    for name, w in zip(model_names, weights_tuple)
                }
                
                # Temporarily set weights
                old_weights = self.weights.copy()
                self.weights = weights_dict
                
                # Get predictions
                pred = self.predict(X_val)['ensemble']
                
                # Calculate error
                mse = mean_squared_error(y_val, pred)
                
                if mse < best_score:
                    best_score = mse
                    best_weights = weights_dict
                
                # Restore weights
                self.weights = old_weights
        
        elif method == 'minimize':
            from scipy.optimize import minimize
            
            def objective(weights):
                # Normalize
                total = sum(weights)
                if total == 0:
                    return float('inf')
                
                weights_dict = {
                    name: w / total
                    for name, w in zip(model_names, weights)
                }
                
                # Temporarily set weights
                old_weights = self.weights.copy()
                self.weights = weights_dict
                
                # Get predictions
                pred = self.predict(X_val)['ensemble']
                
                # Calculate error
                mse = mean_squared_error(y_val, pred)
                
                # Restore weights
                self.weights = old_weights
                
                return mse
            
            # Initial guess: equal weights
            x0 = np.ones(len(model_names)) / len(model_names)
            
            # Bounds: weights between 0 and 1
            bounds = [(0, 1) for _ in model_names]
            
            # Constraint: weights sum to 1
            constraint = {'type': 'eq', 'fun': lambda w: sum(w) - 1}
            
            result = minimize(objective, x0, bounds=bounds, constraints=constraint)
            
            if result.success:
                best_weights = {
                    name: w
                    for name, w in zip(model_names, result.x)
                }
                best_score = result.fun
        
        if best_weights:
            self.weights = best_weights
            logger.info(f"Optimized weights: {best_weights}, MSE: {best_score:.6f}")
        else:
            logger.warning("Weight optimization failed")
        
        return self.weights
