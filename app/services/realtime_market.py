"""
Real-time Market Data Service
Provides direct yfinance integration for searching and fetching live stock data.
No database dependency for basic search and market overview.
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.database import get_db_context

logger = logging.getLogger(__name__)


class RealtimeMarketService:
    """
    Service for fetching real-time stock data from yfinance.
    Works without requiring pre-populated database.
    """
    
    # Popular Indian stocks for market movers (Nifty 50 constituents)
    NIFTY_50 = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
        "SUNPHARMA", "BAJFINANCE", "HCLTECH", "WIPRO", "NTPC",
        "POWERGRID", "TATASTEEL", "M&M", "ULTRACEMCO", "NESTLEIND",
        "JSWSTEEL", "TECHM", "INDUSINDBK", "BAJAJFINSV", "ONGC",
        "TATAMOTORS", "ADANIENT", "ADANIPORTS", "COALINDIA", "HINDALCO",
        "DRREDDY", "CIPLA", "BPCL", "GRASIM", "DIVISLAB",
        "APOLLOHOSP", "EICHERMOT", "BRITANNIA", "HEROMOTOCO", "SBILIFE",
        "TATACONSUM", "HDFCLIFE", "BAJAJ-AUTO", "UPL", "SHREECEM"
    ]
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 60  # Cache for 60 seconds
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if not expired."""
        if key in self._cache and key in self._cache_time:
            if datetime.now() - self._cache_time[key] < timedelta(seconds=self._cache_duration):
                return self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: any):
        """Set cache with timestamp."""
        self._cache[key] = data
        self._cache_time[key] = datetime.now()
    
    def search_stock(self, query: str) -> List[Dict]:
        """
        Search for stocks by name or symbol.
        Searches common Indian stocks first, then tries yfinance.
        
        Args:
            query: Search query (symbol or company name)
            
        Returns:
            List of matching stocks with their info
        """
        results = []
        query_upper = query.upper().strip()
        
        # First, check if it's a direct symbol match
        for symbol in self.NIFTY_50:
            if query_upper in symbol or symbol in query_upper:
                stock_data = self.get_stock_quote(symbol)
                if stock_data:
                    results.append(stock_data)
        
        # Also try direct yfinance lookup
        if len(results) < 5:
            direct_data = self.get_stock_quote(query_upper)
            if direct_data and not any(r['symbol'] == direct_data['symbol'] for r in results):
                results.insert(0, direct_data)
        
        return results[:10]  # Return max 10 results
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote for a stock.
        
        Args:
            symbol: Stock symbol (e.g., RELIANCE or RELIANCE.NS)
            
        Returns:
            Dictionary with stock quote data
        """
        # Add .NS suffix if not present
        yf_symbol = symbol if '.' in symbol else f"{symbol}.NS"
        
        cache_key = f"quote_{yf_symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                # Try with .BO suffix for BSE
                yf_symbol_bse = symbol if '.' in symbol else f"{symbol}.BO"
                ticker = yf.Ticker(yf_symbol_bse)
                info = ticker.info
                
                if not info or 'symbol' not in info:
                    return None
                yf_symbol = yf_symbol_bse
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose') or current_price
            
            change_value = current_price - previous_close if previous_close else 0
            change_percent = (change_value / previous_close * 100) if previous_close else 0
            
            result = {
                'symbol': yf_symbol,
                'display_symbol': symbol.replace('.NS', '').replace('.BO', ''),
                'name': info.get('longName') or info.get('shortName') or symbol,
                'current_price': round(current_price, 2),
                'previous_close': round(previous_close, 2),
                'change_value': round(change_value, 2),
                'change_percent': round(change_percent, 2),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume') or info.get('regularMarketVolume') or 0,
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh') or current_price,
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow') or current_price,
                'week_52_high': info.get('fiftyTwoWeekHigh', 0),
                'week_52_low': info.get('fiftyTwoWeekLow', 0),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'exchange': 'NSE' if '.NS' in yf_symbol else 'BSE',
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching quote for {yf_symbol}: {e}")
            return None
    
    def get_market_movers(self, mover_type: str = 'gainers', limit: int = 10) -> List[Dict]:
        """
        Get top gainers/losers from Nifty 50.
        
        Args:
            mover_type: 'gainers' or 'losers'
            limit: Number of results
            
        Returns:
            List of stock data sorted by change percentage
        """
        cache_key = f"movers_{mover_type}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        stocks_data = []
        
        # Fetch data concurrently
        futures = {
            self.executor.submit(self.get_stock_quote, symbol): symbol
            for symbol in self.NIFTY_50[:30]  # Limit to top 30 for speed
        }
        
        for future in as_completed(futures, timeout=30):
            try:
                data = future.result()
                if data and data.get('current_price', 0) > 0:
                    stocks_data.append(data)
            except Exception as e:
                logger.warning(f"Error in concurrent fetch: {e}")
        
        # Sort by change percent
        if mover_type == 'gainers':
            stocks_data.sort(key=lambda x: x.get('change_percent', 0), reverse=True)
            stocks_data = [s for s in stocks_data if s.get('change_percent', 0) > 0]
        else:
            stocks_data.sort(key=lambda x: x.get('change_percent', 0))
            stocks_data = [s for s in stocks_data if s.get('change_percent', 0) < 0]
        
        result = stocks_data[:limit]
        self._set_cache(cache_key, result)
        return result
    
    def get_all_nifty_stocks(self) -> List[Dict]:
        """Get all Nifty 50 stocks with current data."""
        cache_key = "all_nifty"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        stocks_data = []
        
        # Fetch data concurrently
        futures = {
            self.executor.submit(self.get_stock_quote, symbol): symbol
            for symbol in self.NIFTY_50
        }
        
        for future in as_completed(futures, timeout=60):
            try:
                data = future.result()
                if data:
                    stocks_data.append(data)
            except Exception as e:
                logger.warning(f"Error in fetch: {e}")
        
        # Sort by market cap
        stocks_data.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        self._set_cache(cache_key, stocks_data)
        return stocks_data
    
    def get_stock_history(self, symbol: str, period: str = '1mo') -> Optional[Dict]:
        """
        Get historical data for a stock.
        
        Args:
            symbol: Stock symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '1y')
            
        Returns:
            Dictionary with historical data
        """
        yf_symbol = symbol if '.' in symbol else f"{symbol}.NS"
        
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            df.reset_index(inplace=True)
            
            history = []
            for _, row in df.iterrows():
                history.append({
                    'date': row['Date'].strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                })
            
            return {
                'symbol': yf_symbol,
                'period': period,
                'data': history
            }
            
        except Exception as e:
            logger.error(f"Error fetching history for {yf_symbol}: {e}")
            return None
    
    def ensure_stock_in_db(self, symbol: str) -> Optional[int]:
        """
        Ensure a stock exists in database (for trading).
        Creates it if not exists using real-time data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock ID if successful
        """
        quote = self.get_stock_quote(symbol)
        if not quote:
            return None
        
        try:
            with get_db_context() as db:
                # Check if exists
                stock = db.query(Stock).filter(Stock.symbol == quote['symbol']).first()
                
                if stock:
                    # Update current price
                    stock.current_price = quote['current_price']
                    stock.updated_at = datetime.utcnow()
                    db.commit()
                    return stock.id
                
                # Create new stock
                stock = Stock(
                    symbol=quote['symbol'],
                    name=quote['name'],
                    exchange=quote['exchange'],
                    sector=quote.get('sector', 'Unknown'),
                    industry=quote.get('industry', 'Unknown'),
                    market_cap=quote.get('market_cap', 0),
                    current_price=quote['current_price'],
                    is_active=True
                )
                db.add(stock)
                db.commit()
                db.refresh(stock)
                return stock.id
                
        except Exception as e:
            logger.error(f"Error ensuring stock in DB: {e}")
            return None
    
    def get_stock_id_for_trading(self, symbol: str) -> Tuple[Optional[int], Optional[Dict]]:
        """
        Get stock ID and quote for trading.
        Ensures stock exists in database.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (stock_id, quote_data)
        """
        quote = self.get_stock_quote(symbol)
        if not quote:
            return None, None
        
        stock_id = self.ensure_stock_in_db(symbol)
        return stock_id, quote


# Global instance
_service = None


def get_realtime_service() -> RealtimeMarketService:
    """Get or create global service instance."""
    global _service
    if _service is None:
        _service = RealtimeMarketService()
    return _service
