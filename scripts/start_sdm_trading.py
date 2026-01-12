#!/usr/bin/env python3
"""
Start SDM Trading System for WEEX AI Wars Hackathon

This script starts the Semantic Dataflow Machine trading engine.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from alphagenesis.sdm import SDMTradingEngine


def setup_logging():
    """Configure logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.remove()  # Remove default handler

    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # File logging
    logger.add(
        "logs/sdm_trading_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG"
    )

    logger.info("Logging configured")


def check_environment():
    """Check that required environment variables are set."""
    required_vars = [
        'WEEX_API_KEY',
        'WEEX_API_SECRET',
        'WEEX_API_PASSPHRASE'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set them in .env file or environment")
        return False

    logger.info("✓ All required environment variables present")
    return True


def print_banner():
    """Print startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║           SEMANTIC DATAFLOW MACHINE TRADING SYSTEM                ║
    ║                                                                   ║
    ║                   WEEX AI Wars: Alpha Awakens                     ║
    ║                                                                   ║
    ║  Paradigm: Intent-Driven Post-Von Neumann Architecture           ║
    ║  Features: Self-Learning, Adaptive, Ethically-Constrained        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()

    # Print banner
    print_banner()

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Get configuration
    initial_capital = float(os.getenv('INITIAL_CAPITAL', '1000.0'))
    update_interval = int(os.getenv('UPDATE_INTERVAL', '300'))  # 5 minutes

    logger.info(f"Configuration:")
    logger.info(f"  Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"  Update Interval: {update_interval}s ({update_interval/60:.1f} minutes)")

    # Create and start engine
    try:
        engine = SDMTradingEngine(
            initial_capital=initial_capital,
            update_interval=update_interval
        )

        logger.info("\nStarting SDM Trading Engine...")
        engine.start()

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
