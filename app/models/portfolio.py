"""
Portfolio model for tracking user stock holdings in paper trading.
Tracks positions, average buy price, and unrealized P&L.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Portfolio(Base):
    """
    User portfolio holdings table.
    Tracks stock positions and calculates unrealized gains/losses.
    """
    __tablename__ = "portfolios"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stock_id = Column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Position Data
    quantity = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of shares held"
    )
    average_buy_price = Column(
        Float,
        nullable=False,
        comment="Average purchase price per share"
    )
    
    # Current Market Data (denormalized for performance)
    current_price = Column(
        Float,
        comment="Latest market price (updated periodically)"
    )
    
    # Calculated Metrics
    invested_value = Column(
        Float,
        comment="Total invested = quantity * average_buy_price"
    )
    current_value = Column(
        Float,
        comment="Current value = quantity * current_price"
    )
    unrealized_pnl = Column(
        Float,
        comment="Unrealized P&L = current_value - invested_value"
    )
    unrealized_pnl_percent = Column(
        Float,
        comment="Unrealized P&L percentage"
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
    user = relationship("User", back_populates="portfolios")
    stock = relationship("Stock")
    
    # Composite indexes
    __table_args__ = (
        # Unique constraint: one position per user per stock
        Index('idx_user_stock_unique', 'user_id', 'stock_id', unique=True),
        
        # Query user portfolios with active positions
        Index('idx_user_quantity', 'user_id', 'quantity'),
    )
    
    def __repr__(self):
        return (f"<Portfolio(user_id={self.user_id}, stock_id={self.stock_id}, "
                f"quantity={self.quantity}, pnl={self.unrealized_pnl})>")
    
    def to_dict(self, include_stock_details=False):
        """Convert model to dictionary for API responses"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "stock_id": self.stock_id,
            "quantity": self.quantity,
            "average_buy_price": round(self.average_buy_price, 2),
            "current_price": round(self.current_price, 2) if self.current_price else None,
            "invested_value": round(self.invested_value, 2) if self.invested_value else None,
            "current_value": round(self.current_value, 2) if self.current_value else None,
            "unrealized_pnl": round(self.unrealized_pnl, 2) if self.unrealized_pnl else None,
            "unrealized_pnl_percent": round(self.unrealized_pnl_percent, 2) if self.unrealized_pnl_percent else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_stock_details and self.stock:
            data["stock"] = self.stock.to_dict()
        
        return data
    
    def update_metrics(self, current_price: float = None):
        """
        Update calculated metrics based on current market price.
        Call this whenever stock price updates.
        """
        if current_price:
            self.current_price = current_price
        
        if self.current_price and self.quantity > 0:
            self.invested_value = self.quantity * self.average_buy_price
            self.current_value = self.quantity * self.current_price
            self.unrealized_pnl = self.current_value - self.invested_value
            
            if self.invested_value > 0:
                self.unrealized_pnl_percent = (
                    self.unrealized_pnl / self.invested_value
                ) * 100
            else:
                self.unrealized_pnl_percent = 0.0
    
    def add_shares(self, quantity: int, price: float):
        """
        Add shares to position and recalculate average buy price.
        
        Args:
            quantity: Number of shares to add
            price: Purchase price per share
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        total_cost = self.quantity * self.average_buy_price
        new_cost = quantity * price
        
        self.quantity += quantity
        self.average_buy_price = (total_cost + new_cost) / self.quantity
        
        self.update_metrics()
    
    def remove_shares(self, quantity: int) -> bool:
        """
        Remove shares from position (for selling).
        
        Args:
            quantity: Number of shares to remove
            
        Returns:
            True if successful, False if insufficient shares
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if quantity > self.quantity:
            return False
        
        self.quantity -= quantity
        
        # If all shares sold, reset average buy price
        if self.quantity == 0:
            self.average_buy_price = 0.0
        
        self.update_metrics()
        return True
