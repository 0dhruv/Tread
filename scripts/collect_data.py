"""
Data Collection Script
Standalone script to populate database with Indian stock market data.
Run this initially to seed the database with stock information and historical prices.

Usage:
    python scripts/collect_data.py --stocks 50 --days 365
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data_collector import MarketDataCollector
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_data(num_stocks: int = None, days: int = 365):
    """
    Collect market data for Indian stocks.
    
    Args:
        num_stocks: Number of stocks to collect (None = all)
        days: Number of days of historical data
    """
    logger.info("Starting data collection...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Create collector
    collector = MarketDataCollector()
    
    # Get stock list
    stock_list = collector.NSE_STOCKS
    if num_stocks:
        stock_list = stock_list[:num_stocks]
    
    logger.info(f"Collecting data for {len(stock_list)} stocks with {days} days of history")
    
    # Collect data
    results = collector.collect_all_stocks(stock_list)
    
    logger.info(f"Collection complete!")
    logger.info(f"Success: {results['success']} stocks")
    logger.info(f"Failed: {results['failed']} stocks")
    
    # Cleanup
    collector.shutdown()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Collect Indian stock market data"
    )
    parser.add_argument(
        '--stocks',
        type=int,
        default=None,
        help='Number of stocks to collect (default: all)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of historical data (default: 365)'
    )
    
    args = parser.parse_args()
    
    collect_data(args.stocks, args.days)


if __name__ == "__main__":
    main()
