"""
Real-time Stock API routes
Provides live stock data from yfinance without database dependency.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.auth import get_current_user
from app.models.user import User
from app.services.realtime_market import get_realtime_service

router = APIRouter(prefix="/realtime", tags=["Real-time Market Data"])


@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="Search query (symbol or name)"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for stocks by name or symbol using real-time data.
    
    Returns matching stocks with current prices and change percentages.
    """
    if not query or len(query.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query must be at least 1 character")
    
    service = get_realtime_service()
    results = service.search_stock(query.strip())
    
    return {
        "query": query,
        "count": len(results),
        "stocks": results
    }


@router.get("/quote/{symbol}")
async def get_stock_quote(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time quote for a specific stock.
    
    Parameters:
        symbol: Stock symbol (e.g., RELIANCE, TCS, INFY)
    """
    service = get_realtime_service()
    quote = service.get_stock_quote(symbol.strip().upper())
    
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")
    
    return quote


@router.get("/movers")
async def get_market_movers(
    mover_type: str = Query("gainers", regex="^(gainers|losers)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Get top gainers or losers from Nifty 50 in real-time.
    
    Parameters:
        mover_type: 'gainers' or 'losers'
        limit: Number of results (max 50)
    """
    service = get_realtime_service()
    stocks = service.get_market_movers(mover_type, limit)
    
    return {
        "mover_type": mover_type,
        "count": len(stocks),
        "stocks": stocks
    }


@router.get("/all-stocks")
async def get_all_stocks(
    current_user: User = Depends(get_current_user)
):
    """
    Get all Nifty 50 stocks with current prices.
    
    Returns a list of all stocks sorted by market cap.
    """
    service = get_realtime_service()
    stocks = service.get_all_nifty_stocks()
    
    return {
        "count": len(stocks),
        "stocks": stocks
    }


@router.get("/history/{symbol}")
async def get_stock_history(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical data for a stock.
    
    Parameters:
        symbol: Stock symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
    """
    service = get_realtime_service()
    history = service.get_stock_history(symbol.strip().upper(), period)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history for '{symbol}'")
    
    return history


@router.post("/prepare-trade/{symbol}")
async def prepare_trade(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Prepare a stock for trading.
    
    Ensures the stock exists in the database and returns current data.
    This is used before executing a buy order for a new stock.
    """
    service = get_realtime_service()
    stock_id, quote = service.get_stock_id_for_trading(symbol.strip().upper())
    
    if not stock_id or not quote:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")
    
    return {
        "stock_id": stock_id,
        "symbol": quote['symbol'],
        "name": quote['name'],
        "current_price": quote['current_price'],
        "change_percent": quote['change_percent']
    }
