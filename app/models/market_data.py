"""
MarketData model for storing daily OHLC (Open, High, Low, Close) price data.
Optimized for time-series analytics and fast range queries.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date

from app.database import Base


class MarketData(Base):
    """
    Time-series market data table for daily stock prices.
    Stores OHLC data with volume and percentage changes.
    
    Design consideration: For production with millions of records,
    consider using TimescaleDB (PostgreSQL extension) for better
    time-series performance.
    """
    __tablename__ = "market_data"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Key
    stock_id = Column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Time dimension
    date = Column(Date, nullable=False, index=True, comment="Trading date")
    
    # OHLC Data
    open_price = Column(Float, nullable=False, comment="Opening price")
    high_price = Column(Float, nullable=False, comment="Highest price")
    low_price = Column(Float, nullable=False, comment="Lowest price")
    close_price = Column(Float, nullable=False, comment="Closing price")
    
    # Volume
    volume = Column(Integer, default=0, comment="Trading volume")
    
    # Calculated metrics (denormalized for performance)
    change_percent = Column(
        Float,
        index=True,
        comment="Percentage change from previous close"
    )
    change_value = Column(Float, comment="Absolute change in price")
    
    # Additional metrics
    avg_price = Column(Float, comment="Average of OHLC")
    vwap = Column(Float, comment="Volume Weighted Average Price")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    stock = relationship("Stock", back_populates="market_data")
    
    # Composite indexes for time-series queries
    __table_args__ = (
        # Unique constraint: one record per stock per day
        Index('idx_stock_date_unique', 'stock_id', 'date', unique=True),
        
        # Query stocks by date range
        Index('idx_date_stock', 'date', 'stock_id'),
        
        # Find stocks with specific percentage changes
        Index('idx_change_percent', 'change_percent', 'date'),
        
        # Combined index for dashboard queries
        Index('idx_date_change', 'date', 'change_percent', 'stock_id'),
    )
    
    def __repr__(self):
        return (f"<MarketData(stock_id={self.stock_id}, date={self.date}, "
                f"close={self.close_price}, change={self.change_percent}%)>")
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "stock_id": self.stock_id,
            "date": self.date.isoformat() if isinstance(self.date, date) else self.date,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "change_percent": round(self.change_percent, 2) if self.change_percent else None,
            "change_value": round(self.change_value, 2) if self.change_value else None,
            "avg_price": round(self.avg_price, 2) if self.avg_price else None,
            "vwap": round(self.vwap, 2) if self.vwap else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def calculate_change(current_close: float, previous_close: float) -> tuple:
        """
        Calculate percentage and absolute change.
        Returns: (change_percent, change_value)
        """
        if not previous_close or previous_close == 0:
            return (0.0, 0.0)
        
        change_value = current_close - previous_close
        change_percent = (change_value / previous_close) * 100
        
        return (change_percent, change_value)
    
    @staticmethod
    def calculate_vwap(high: float, low: float, close: float, volume: int) -> float:
        """
        Calculate Volume Weighted Average Price.
        VWAP = (High + Low + Close) / 3 * Volume / Total Volume
        
        Note: This is simplified. Production implementation would
        calculate across intraday data.
        """
        if volume == 0:
            return (high + low + close) / 3
        
        typical_price = (high + low + close) / 3
        return typical_price
