"""
Stock and Market Data API routes
Provides access to stock information, market data, and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.database import get_db
from app.models.stock import Stock
from app.models.market_data import MarketData
from app.api.schemas import (
    StockResponse,
    StockList,
    MarketDataResponse,
    StockWithLatestData,
    MarketMoversRequest,
    MarketMoversResponse,
    PriceChangeFilter
)
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])


@router.get("/", response_model=StockList)
async def get_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sector: Optional[str] = None,
    exchange: Optional[str] = None,
    min_market_cap: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of stocks with pagination and filters.
    
    Filters:
    - search: Search by symbol or name
    - sector: Filter by sector
    - exchange: Filter by exchange (NSE/BSE)
    - min_market_cap: Minimum market capitalization
    """
    query = db.query(Stock).filter(Stock.is_active == True)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Stock.symbol.ilike(search_pattern),
                Stock.name.ilike(search_pattern)
            )
        )
    
    if sector:
        query = query.filter(Stock.sector == sector)
    
    if exchange:
        query = query.filter(Stock.exchange == exchange)
    
    if min_market_cap:
        query = query.filter(Stock.market_cap >= min_market_cap)
    
    # Count total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    stocks = query.order_by(Stock.market_cap.desc()).offset(offset).limit(page_size).all()
    
    return {
        "stocks": stocks,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{stock_id}", response_model=StockResponse)
async def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific stock.
    """
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return stock


@router.get("/{stock_id}/history", response_model=List[MarketDataResponse])
async def get_stock_history(
    stock_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get historical market data for a stock.
    
    Parameters:
    - days: Number of days of historical data (max 365)
    """
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    start_date = datetime.now() - timedelta(days=days)
    
    market_data = db.query(MarketData).filter(
        and_(
            MarketData.stock_id == stock_id,
            MarketData.date >= start_date.date()
        )
    ).order_by(MarketData.date.desc()).all()
    
    return market_data


@router.get("/market/movers")
async def get_market_movers(
    mover_type: str = Query("gainers", regex="^(gainers|losers|active)$"),
    limit: int = Query(20, ge=1, le=100),
    min_change: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get market movers (top gainers/losers/most active).
    
    Parameters:
    - mover_type: "gainers", "losers", or "active"
    - limit: Number of results (max 100)
    - min_change: Minimum change percentage (optional)
    """
    today = date.today()
    
    # Subquery to get latest market data for each stock
    latest_data_subquery = db.query(
        MarketData.stock_id,
        func.max(MarketData.date).label('max_date')
    ).group_by(MarketData.stock_id).subquery()
    
    # Join stocks with their latest market data
    query = db.query(Stock, MarketData).join(
        MarketData,
        Stock.id == MarketData.stock_id
    ).join(
        latest_data_subquery,
        and_(
            MarketData.stock_id == latest_data_subquery.c.stock_id,
            MarketData.date == latest_data_subquery.c.max_date
        )
    ).filter(Stock.is_active == True)
    
    # Apply filters based on mover type
    if mover_type == "gainers":
        query = query.filter(MarketData.change_percent > 0)
        if min_change:
            query = query.filter(MarketData.change_percent >= min_change)
        query = query.order_by(MarketData.change_percent.desc())
    
    elif mover_type == "losers":
        query = query.filter(MarketData.change_percent < 0)
        if min_change:
            query = query.filter(MarketData.change_percent <= -min_change)
        query = query.order_by(MarketData.change_percent.asc())
    
    else:  # active
        query = query.order_by(MarketData.volume.desc())
    
    results = query.limit(limit).all()
    
    # Format response
    stocks_with_data = []
    for stock, market_data in results:
        stock_dict = stock.to_dict()
        stock_dict['latest_data'] = market_data.to_dict()
        stocks_with_data.append(stock_dict)
    
    return {
        "stocks": stocks_with_data,
        "mover_type": mover_type,
        "count": len(stocks_with_data)
    }


@router.get("/market/sectors")
async def get_sector_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance summary by sector.
    """
    # Subquery for latest market data
    latest_data_subquery = db.query(
        MarketData.stock_id,
        func.max(MarketData.date).label('max_date')
    ).group_by(MarketData.stock_id).subquery()
    
    # Get sector performance
    sector_stats = db.query(
        Stock.sector,
        func.avg(MarketData.change_percent).label('avg_change'),
        func.count(Stock.id).label('num_stocks')
    ).join(
        MarketData,
        Stock.id == MarketData.stock_id
    ).join(
        latest_data_subquery,
        and_(
            MarketData.stock_id == latest_data_subquery.c.stock_id,
            MarketData.date == latest_data_subquery.c.max_date
        )
    ).filter(
        Stock.is_active == True,
        Stock.sector.isnot(None)
    ).group_by(Stock.sector).all()
    
    return [
        {
            "sector": sector,
            "avg_change": round(avg_change, 2),
            "num_stocks": num_stocks
        }
        for sector, avg_change, num_stocks in sector_stats
    ]


@router.get("/analytics/price-change")
async def get_stocks_by_price_change(
    change_percent: float = Query(..., description="Target change percentage (e.g., 2, 5, 10)"),
    tolerance: float = Query(0.5, description="Tolerance range (default 0.5%)"),
    date_filter: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get stocks with specific price change percentage.
    
    Examples:
    - change_percent=2, tolerance=0.5 → stocks between 1.5% and 2.5%
    - change_percent=-5, tolerance=0.5 → stocks between -5.5% and -4.5%
    
    This is useful for analytics dashboards showing 2%, 5%, 10%, 15% movers.
    """
    min_change = change_percent - tolerance
    max_change = change_percent + tolerance
    
    # Determine date
    target_date = date_filter if date_filter else date.today()
    
    # Query stocks with matching change
    results = db.query(Stock, MarketData).join(
        MarketData,
        Stock.id == MarketData.stock_id
    ).filter(
        and_(
            Stock.is_active == True,
            MarketData.date == target_date,
            MarketData.change_percent >= min_change,
            MarketData.change_percent <= max_change
        )
    ).order_by(MarketData.change_percent.desc()).all()
    
    stocks_data = []
    for stock, market_data in results:
        stock_dict = stock.to_dict()
        stock_dict['latest_data'] = market_data.to_dict()
        stocks_data.append(stock_dict)
    
    return {
        "target_change": change_percent,
        "tolerance": tolerance,
        "date": target_date,
        "count": len(stocks_data),
        "stocks": stocks_data
    }


@router.get("/search/symbols")
async def search_symbols(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Quick search for stock symbols and names.
    Useful for autocomplete features.
    """
    search_pattern = f"%{query}%"
    
    stocks = db.query(Stock).filter(
        and_(
            Stock.is_active == True,
            or_(
                Stock.symbol.ilike(search_pattern),
                Stock.name.ilike(search_pattern)
            )
        )
    ).limit(limit).all()
    
    return [
        {
            "id": stock.id,
            "symbol": stock.symbol,
            "name": stock.name,
            "current_price": stock.current_price
        }
        for stock in stocks
    ]
