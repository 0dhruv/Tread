"""
Stock model representing individual stocks in the Indian market.
Stores metadata like ticker symbol, company name, sector, and market cap.
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Stock(Base):
    """
    Stock table storing metadata for Indian stocks (NSE/BSE).
    ~7500+ stocks supported.
    """
    __tablename__ = "stocks"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Stock Identification
    symbol = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Stock ticker symbol (e.g., RELIANCE.NS)"
    )
    name = Column(String(200), nullable=False, comment="Company name")
    exchange = Column(
        String(10),
        nullable=False,
        index=True,
        comment="Exchange: NSE or BSE"
    )
    
    # Classification
    sector = Column(String(100), index=True, comment="Industry sector")
    industry = Column(String(100), comment="Specific industry")
    
    # Market Data
    market_cap = Column(
        Float,
        index=True,
        comment="Market capitalization in INR"
    )
    current_price = Column(Float, comment="Latest traded price")
    
    # Stock Status
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="Whether stock is actively trading"
    )
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    market_data = relationship(
        "MarketData",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Composite indexes for frequent queries
    __table_args__ = (
        Index('idx_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_market_cap_sector', 'market_cap', 'sector'),
        Index('idx_active_stocks', 'is_active', 'market_cap'),
    )
    
    def __repr__(self):
        return f"<Stock(symbol={self.symbol}, name={self.name}, market_cap={self.market_cap})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "current_price": self.current_price,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
