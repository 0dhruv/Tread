"""
Pydantic schemas for request/response validation.
Ensures type safety and automatic API documentation.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum() or '_' in v, 'Username must be alphanumeric'
        return v


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None


class UserResponse(BaseModel):
    """User profile response"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    paper_balance: float
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


# ============================================================================
# Stock Schemas
# ============================================================================

class StockBase(BaseModel):
    """Base stock information"""
    symbol: str
    name: str
    exchange: str
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[float]
    current_price: Optional[float]


class StockResponse(StockBase):
    """Stock information response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class StockList(BaseModel):
    """List of stocks with pagination"""
    stocks: List[StockResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Market Data Schemas
# ============================================================================

class MarketDataResponse(BaseModel):
    """Market data (OHLC) response"""
    id: int
    stock_id: int
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    change_percent: Optional[float]
    change_value: Optional[float]
    
    class Config:
        orm_mode = True


class StockWithLatestData(StockResponse):
    """Stock with latest market data"""
    latest_data: Optional[MarketDataResponse]


class MarketMoverType(str, Enum):
    """Market mover filter types"""
    GAINERS = "gainers"
    LOSERS = "losers"
    ACTIVE = "active"


class MarketMoversRequest(BaseModel):
    """Request for market movers"""
    mover_type: MarketMoverType
    min_change_percent: Optional[float] = None
    limit: int = Field(default=20, ge=1, le=100)


class MarketMoversResponse(BaseModel):
    """Market movers response"""
    stocks: List[StockWithLatestData]
    mover_type: str
    count: int


# ============================================================================
# Trading Schemas
# ============================================================================

class TransactionTypeEnum(str, Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


class TradeRequest(BaseModel):
    """Buy/Sell trade request"""
    stock_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class TransactionResponse(BaseModel):
    """Transaction response"""
    id: int
    stock_id: int
    transaction_type: str
    quantity: int
    price: float
    total_value: float
    transaction_fee: float
    net_amount: float
    realized_pnl: Optional[float]
    balance_after: float
    created_at: datetime
    
    class Config:
        orm_mode = True


class PortfolioHolding(BaseModel):
    """Portfolio holding response"""
    id: int
    stock_id: int
    quantity: int
    average_buy_price: float
    current_price: float
    invested_value: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    stock: Optional[StockResponse]
    
    class Config:
        orm_mode = True


class PortfolioSummary(BaseModel):
    """Complete portfolio summary"""
    user_id: int
    cash_balance: float
    invested_value: float
    current_value: float
    total_portfolio_value: float
    holdings: List[PortfolioHolding]
    pnl: dict
    num_positions: int


class TransactionHistory(BaseModel):
    """Transaction history response"""
    transactions: List[TransactionResponse]
    total_count: int
    limit: int
    offset: int


# ============================================================================
# Analytics Schemas
# ============================================================================

class PriceChangeFilter(BaseModel):
    """Filter for stocks by price change percentage"""
    min_change: Optional[float] = None
    max_change: Optional[float] = None
    date: Optional[date] = None


class StockPerformanceResponse(BaseModel):
    """Stock performance metrics"""
    stock: StockResponse
    performance_data: List[MarketDataResponse]
    metrics: dict  # Additional calculated metrics


class SectorPerformance(BaseModel):
    """Sector performance summary"""
    sector: str
    avg_change: float
    num_stocks: int
    top_performers: List[StockResponse]


# ============================================================================
# AI Assistant Schemas
# ============================================================================

class AIAnalysisRequest(BaseModel):
    """Request for AI stock analysis"""
    stock_id: int
    user_query: Optional[str] = None


class AIAnalysisResponse(BaseModel):
    """AI analysis response"""
    analysis: str
    status: str
    timestamp: datetime
    stock_symbol: Optional[str]


class AIChatRequest(BaseModel):
    """AI chat request"""
    message: str
    context: Optional[dict] = None


class AIChatResponse(BaseModel):
    """AI chat response"""
    response: str
    status: str
    timestamp: datetime


# ============================================================================
# Dashboard Schemas
# ============================================================================

class DashboardSummary(BaseModel):
    """Dashboard overview data"""
    user_portfolio: PortfolioSummary
    market_movers: dict
    ai_insights: Optional[str]
    top_gainers: List[StockWithLatestData]
    top_losers: List[StockWithLatestData]
    recent_transactions: List[TransactionResponse]
