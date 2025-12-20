"""
Configuration Management

Handles configuration loading and management for AlphaGenesis.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv
from loguru import logger


class Config:
    """
    Configuration manager for AlphaGenesis.
    
    Loads configuration from environment variables, YAML files,
    and provides a unified interface for accessing settings.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to YAML configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self._config: Dict[str, Any] = {}
        
        # Load from YAML file if provided
        if config_file and Path(config_file).exists():
            self.load_yaml(config_file)
        
        # Override with environment variables
        self._load_env_vars()
    
    def load_yaml(self, config_file: str):
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to YAML file
        """
        try:
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    self._config.update(yaml_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
    
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        env_mappings = {
            "WEEX_API_KEY": ("weex", "api_key"),
            "WEEX_API_SECRET": ("weex", "api_secret"),
            "WEEX_API_PASSPHRASE": ("weex", "api_passphrase"),
            "WEEX_BASE_URL": ("weex", "base_url"),
            "DATABASE_URL": ("database", "url"),
            "REDIS_URL": ("redis", "url"),
            "MODEL_CHECKPOINT_DIR": ("model", "checkpoint_dir"),
            "MODEL_DEVICE": ("model", "device"),
            "MAX_POSITION_SIZE": ("risk", "max_position_size"),
            "MAX_LEVERAGE": ("risk", "max_leverage"),
            "STOP_LOSS_PERCENT": ("risk", "stop_loss_percent"),
            "INITIAL_CAPITAL": ("backtest", "initial_capital"),
            "COMMISSION_RATE": ("backtest", "commission_rate"),
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FILE": ("logging", "file"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if section not in self._config:
                    self._config[section] = {}
                
                # Convert numeric strings to appropriate types
                if value.replace('.', '').isdigit():
                    value = float(value) if '.' in value else int(value)
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                self._config[section][key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Supports dot notation for nested keys (e.g., 'weex.api_key').
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get all configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
    
    def save_yaml(self, config_file: str):
        """
        Save configuration to YAML file.
        
        Args:
            config_file: Path to save YAML file
        """
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            
            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config file {config_file}: {e}")


# Global configuration instance
_global_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get global configuration instance.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Config instance
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(config_file)
    
    return _global_config
