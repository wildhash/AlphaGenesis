# AlphaGenesis 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20management-poetry-blue)](https://python-poetry.org/)

An institutional-grade, AI-powered quantitative trading system engineered to generate sustainable alpha in volatile crypto markets. Built for the WEEX AI Wars Hackathon, AlphaGenesis combines cutting-edge machine learning with sophisticated risk management to deliver professional-grade trading capabilities.

## 🌟 Key Features

### Advanced Machine Learning Models
- **LSTM Networks**: Deep learning for time series prediction with multi-layer architecture
- **Transformer Models**: State-of-the-art attention mechanisms for capturing long-range dependencies
- **Reinforcement Learning**: Adaptive trading agents using PPO, A2C, and DQN algorithms

### Sophisticated Risk Management
- **Value at Risk (VaR)**: Multiple calculation methods (Historical, Parametric, Monte Carlo)
- **GARCH Volatility Modeling**: Time-varying volatility forecasting for dynamic risk assessment
- **Portfolio Optimization**: Mean-variance optimization, risk parity, and maximum Sharpe ratio
- **Position Sizing**: Advanced algorithms based on Kelly Criterion and risk-adjusted returns

### Event-Driven Backtesting
- Realistic simulation with slippage and transaction costs
- Order book modeling and market impact
- Comprehensive performance metrics (Sharpe, Sortino, Calmar ratios)
- Maximum drawdown analysis and equity curve visualization

### Professional Infrastructure
- **WEEX Exchange Integration**: Native API support with WebSocket streaming
- **Modular Architecture**: Clean separation of concerns for maintainability
- **Production-Ready**: Comprehensive logging, error handling, and monitoring
- **Type-Safe**: Full type annotations for code quality

## 📁 Project Structure

```
AlphaGenesis/
├── alphagenesis/              # Main package
│   ├── data/                  # Data pipeline & WEEX API integration
│   │   ├── weex_client.py     # Exchange API client
│   │   ├── data_fetcher.py    # Data acquisition
│   │   └── data_storage.py    # Persistent storage
│   ├── features/              # Feature engineering
│   │   ├── technical_indicators.py  # Technical analysis
│   │   └── feature_engineer.py      # Feature creation
│   ├── models/                # Machine learning models
│   │   ├── lstm_model.py      # LSTM implementation
│   │   ├── transformer_model.py     # Transformer architecture
│   │   └── rl_agent.py        # Reinforcement learning
│   ├── risk/                  # Risk management
│   │   ├── var_calculator.py  # VaR calculations
│   │   ├── garch_model.py     # GARCH volatility
│   │   ├── portfolio_optimizer.py   # Portfolio optimization
│   │   └── risk_manager.py    # Central risk engine
│   ├── backtest/              # Backtesting framework
│   │   ├── backtester.py      # Event-driven engine
│   │   └── performance_metrics.py   # Performance analysis
│   ├── execution/             # Order execution
│   │   ├── order_executor.py  # Trade execution
│   │   └── order_manager.py   # Order lifecycle management
│   └── utils/                 # Utilities
│       ├── logger.py          # Logging configuration
│       └── config.py          # Configuration management
├── config/                    # Configuration files
│   └── config.yaml            # Main configuration
├── notebooks/                 # Jupyter notebooks
├── scripts/                   # Utility scripts
│   └── example_usage.py       # Usage examples
├── tests/                     # Test suite
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── pyproject.toml            # Poetry dependencies
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- WEEX exchange API credentials (for live trading)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/wildhash/AlphaGenesis-.git
cd AlphaGenesis-
```

2. **Install Poetry** (if not already installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies**
```bash
poetry install
```

For additional features:
```bash
# Install with TA-Lib support
poetry install --extras talib

# Install with Zipline support
poetry install --extras zipline
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your WEEX API credentials
```

5. **Activate the virtual environment**
```bash
poetry shell
```

### Basic Usage

```python
from alphagenesis.data import WEEXClient, DataFetcher
from alphagenesis.features import FeatureEngineer
from alphagenesis.models import LSTMModel
from alphagenesis.risk import RiskManager
from alphagenesis.backtest import Backtester

# Fetch market data
weex_client = WEEXClient()
data_fetcher = DataFetcher(weex_client)
df = data_fetcher.fetch_ohlcv("BTC/USDT", interval="1h")

# Engineer features
feature_engineer = FeatureEngineer()
df_with_features = feature_engineer.create_features(df)

# Initialize risk manager
risk_manager = RiskManager(
    max_position_size=0.1,
    max_leverage=3.0,
    stop_loss_pct=0.02
)

# Run backtest
backtester = Backtester(initial_capital=100000)
results = backtester.run(df, strategy_function, symbol="BTC/USDT")
```

### Run Example Script

```bash
poetry run python scripts/example_usage.py
```

## 🏗️ Architecture Overview

### Data Pipeline
The data module handles all interaction with the WEEX exchange:
- Real-time and historical market data fetching
- WebSocket connections for live streaming
- Data validation and cleaning
- Persistent storage with multiple backends (Parquet, HDF5, PostgreSQL)

### Feature Engineering
Comprehensive technical indicator library:
- **Momentum**: RSI, Stochastic, Rate of Change
- **Trend**: Moving Averages (SMA, EMA), MACD
- **Volatility**: Bollinger Bands, ATR, Historical Volatility
- **Volume**: Volume indicators and price-volume trends
- **Custom**: Domain-specific features for crypto markets

### Machine Learning Models

#### LSTM Networks
```python
from alphagenesis.models import LSTMModel

model = LSTMModel(
    input_size=50,
    hidden_size=128,
    num_layers=2,
    output_size=1
)
```

#### Transformer Models
```python
from alphagenesis.models import TransformerModel

model = TransformerModel(
    input_size=50,
    d_model=128,
    nhead=8,
    num_layers=3
)
```

#### Reinforcement Learning
```python
from alphagenesis.models import RLTradingAgent, TradingEnvironment

env = TradingEnvironment(df, initial_balance=10000)
agent = RLTradingAgent(algorithm="PPO", env=env)
agent.train(total_timesteps=100000)
```

### Risk Management

#### VaR Calculation
```python
from alphagenesis.risk import VaRCalculator

var_calc = VaRCalculator()
var = var_calc.historical_var(returns, confidence_level=0.95)
cvar = var_calc.conditional_var(returns, confidence_level=0.95)
```

#### GARCH Volatility
```python
from alphagenesis.risk import GARCHModel

garch = GARCHModel(p=1, q=1)
garch.fit(returns)
vol_forecast = garch.forecast_volatility(horizon=5)
```

#### Portfolio Optimization
```python
from alphagenesis.risk import PortfolioOptimizer

optimizer = PortfolioOptimizer(returns_df, risk_free_rate=0.02)
result = optimizer.optimize_sharpe()
optimal_weights = result['weights']
```

### Backtesting Engine

Event-driven architecture for realistic simulation:
- Order execution with slippage and commissions
- Position management and P&L tracking
- Real-time equity curve generation
- Comprehensive performance metrics

```python
from alphagenesis.backtest import Backtester, PerformanceMetrics

backtester = Backtester(
    initial_capital=100000,
    commission_rate=0.001,
    slippage_rate=0.0005
)

equity_curve = backtester.run(data, strategy_function)
metrics = PerformanceMetrics.calculate_all_metrics(equity_curve)
```

## 📊 Performance Metrics

AlphaGenesis calculates comprehensive performance metrics:

- **Returns**: Total return, annualized return, log returns
- **Risk Metrics**: Volatility, VaR, CVaR, maximum drawdown
- **Risk-Adjusted Returns**: Sharpe ratio, Sortino ratio, Calmar ratio
- **Trade Statistics**: Win rate, profit factor, average trade P&L
- **Portfolio Metrics**: Turnover, concentration, diversification

## 🔧 Configuration

Configuration is managed through YAML files and environment variables:

```yaml
# config/config.yaml
weex:
  api_key: ${WEEX_API_KEY}
  api_secret: ${WEEX_API_SECRET}

risk:
  max_position_size: 0.1
  max_leverage: 3.0
  stop_loss_percent: 0.02

model:
  device: cuda
  checkpoint_dir: ./models/saved
```

## 🧪 Testing

Run the test suite:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=alphagenesis --cov-report=html
```

## 📚 Documentation

For detailed documentation, see:
- [API Reference](docs/api.md)
- [User Guide](docs/guide.md)
- [Examples](notebooks/)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Setup

For development with code quality tools:

```bash
# Install dev dependencies
poetry install --with dev

# Setup pre-commit hooks
poetry run pre-commit install

# Run linters
poetry run black alphagenesis/
poetry run flake8 alphagenesis/
poetry run mypy alphagenesis/

# Run tests
poetry run pytest
```

## 🔐 Security

- Never commit API keys or secrets to the repository
- Use environment variables for sensitive configuration
- Review the [Security Policy](SECURITY.md) for reporting vulnerabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the WEEX AI Wars Hackathon
- Inspired by institutional quantitative trading systems
- Uses state-of-the-art research in ML and quantitative finance

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wildhash/AlphaGenesis-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wildhash/AlphaGenesis-/discussions)
- **Email**: support@alphagenesis.io

## 🗺️ Roadmap

- [ ] Additional ML models (GRU, Attention mechanisms)
- [ ] Multi-exchange support
- [ ] Real-time strategy monitoring dashboard
- [ ] Advanced order types (iceberg, TWAP, VWAP)
- [ ] Portfolio rebalancing automation
- [ ] Sentiment analysis integration
- [ ] On-chain metrics integration

---

**Built with ❤️ for the WEEX AI Wars Hackathon**

*Disclaimer: This software is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Always do your own research and never invest more than you can afford to lose.*
