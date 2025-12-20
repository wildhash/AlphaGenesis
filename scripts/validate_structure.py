#!/usr/bin/env python3
"""
Validation script to check all required files exist and have correct structure.
"""

import os
from pathlib import Path

def check_file_exists(filepath):
    """Check if file exists and print result."""
    exists = Path(filepath).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists

def main():
    print("=" * 60)
    print("AlphaGenesis Structure Validation")
    print("=" * 60)
    print()
    
    base_path = Path(__file__).parent.parent
    all_exist = True
    
    # Data Pipeline
    print("Data Pipeline:")
    all_exist &= check_file_exists(base_path / "alphagenesis/data/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/data/weex_client.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/data/data_fetcher.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/data/data_cleaner.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/data/data_storage.py")
    print()
    
    # Feature Engineering
    print("Feature Engineering:")
    all_exist &= check_file_exists(base_path / "alphagenesis/features/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/features/technical_indicators.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/features/orderbook.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/features/temporal.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/features/feature_engineer.py")
    print()
    
    # ML Models
    print("ML Models:")
    all_exist &= check_file_exists(base_path / "alphagenesis/models/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/models/lstm_model.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/models/rl_agent.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/models/ensemble.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/models/train_pipeline.py")
    print()
    
    # Risk Engine
    print("Risk Engine:")
    all_exist &= check_file_exists(base_path / "alphagenesis/risk/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/risk/var_calculator.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/risk/garch_model.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/risk/position_sizer.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/risk/circuit_breaker.py")
    print()
    
    # Execution
    print("Execution:")
    all_exist &= check_file_exists(base_path / "alphagenesis/execution/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/execution/order_manager.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/execution/portfolio.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/execution/live_loop.py")
    print()
    
    # Backtester
    print("Backtester:")
    all_exist &= check_file_exists(base_path / "alphagenesis/backtest/__init__.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/backtest/backtester.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/backtest/performance_metrics.py")
    all_exist &= check_file_exists(base_path / "alphagenesis/backtest/metrics_report.py")
    print()
    
    # Configuration
    print("Configuration:")
    all_exist &= check_file_exists(base_path / "config/__init__.py")
    all_exist &= check_file_exists(base_path / "config/settings.py")
    all_exist &= check_file_exists(base_path / "config/constants.py")
    print()
    
    # Scripts
    print("Scripts:")
    all_exist &= check_file_exists(base_path / "scripts/setup_environment.sh")
    all_exist &= check_file_exists(base_path / "scripts/run_backtest.py")
    print()
    
    # Tests
    print("Tests:")
    all_exist &= check_file_exists(base_path / "tests/test_risk_engine.py")
    print()
    
    print("=" * 60)
    if all_exist:
        print("✓ ALL REQUIRED FILES PRESENT")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Install dependencies: poetry install")
        print("2. Configure API keys in .env file")
        print("3. Run setup script: ./scripts/setup_environment.sh")
        print("4. Run backtest: poetry run python scripts/run_backtest.py")
        return 0
    else:
        print("✗ SOME FILES ARE MISSING")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit(main())
