"""
Transaction model for recording all paper trading buy/sell activities.
Maintains complete audit trail of trading history.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class Transaction(Base):
    """
    Transaction history table for paper trading.
    Records all buy/sell operations with complete details.
    """
    __tablename__ = "transactions"
    
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
    
    # Transaction Details
    transaction_type = Column(
        Enum(TransactionType),
        nullable=False,
        index=True,
        comment="BUY or SELL"
    )
    quantity = Column(
        Integer,
        nullable=False,
        comment="Number of shares traded"
    )
    price = Column(
        Float,
        nullable=False,
        comment="Execution price per share"
    )
    
    # Financial Calculations
    total_value = Column(
        Float,
        nullable=False,
        comment="Total transaction value (quantity * price)"
    )
    transaction_fee = Column(
        Float,
        default=0.0,
        comment="Transaction fee/brokerage"
    )
    net_amount = Column(
        Float,
        nullable=False,
        comment="Net amount after fees"
    )
    
    # Realized P&L (for SELL transactions)
    realized_pnl = Column(
        Float,
        comment="Realized profit/loss (only for SELL transactions)"
    )
    average_buy_price = Column(
        Float,
        comment="Average buy price at time of sale (for SELL transactions)"
    )
    
    # Balance after transaction
    balance_after = Column(
        Float,
        comment="User's paper balance after this transaction"
    )
    
    # Metadata
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    notes = Column(String(500), comment="Optional transaction notes")
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    stock = relationship("Stock")
    
    # Composite indexes for analytics
    __table_args__ = (
        # Query user transaction history
        Index('idx_user_created', 'user_id', 'created_at'),
        
        # Query transactions by type and date
        Index('idx_type_date', 'transaction_type', 'created_at'),
        
        # Stock transaction history
        Index('idx_stock_date', 'stock_id', 'created_at'),
    )
    
    def __repr__(self):
        return (f"<Transaction(user_id={self.user_id}, type={self.transaction_type.value}, "
                f"stock_id={self.stock_id}, quantity={self.quantity}, price={self.price})>")
    
    def to_dict(self, include_stock_details=False):
        """Convert model to dictionary for API responses"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "stock_id": self.stock_id,
            "transaction_type": self.transaction_type.value if self.transaction_type else None,
            "quantity": self.quantity,
            "price": round(self.price, 2),
            "total_value": round(self.total_value, 2),
            "transaction_fee": round(self.transaction_fee, 2),
            "net_amount": round(self.net_amount, 2),
            "realized_pnl": round(self.realized_pnl, 2) if self.realized_pnl else None,
            "average_buy_price": round(self.average_buy_price, 2) if self.average_buy_price else None,
            "balance_after": round(self.balance_after, 2) if self.balance_after else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes,
        }
        
        if include_stock_details and self.stock:
            data["stock"] = self.stock.to_dict()
        
        return data
    
    @staticmethod
    def calculate_transaction_fee(total_value: float, fee_percent: float) -> float:
        """
        Calculate transaction fee based on total value.
        
        Args:
            total_value: Total transaction value
            fee_percent: Fee percentage (e.g., 0.0005 for 0.05%)
            
        Returns:
            Transaction fee amount
        """
        return total_value * fee_percent
    
    @staticmethod
    def calculate_realized_pnl(
        sell_price: float,
        avg_buy_price: float,
        quantity: int,
        transaction_fee: float
    ) -> float:
        """
        Calculate realized profit/loss for a SELL transaction.
        
        Args:
            sell_price: Selling price per share
            avg_buy_price: Average buying price per share
            quantity: Number of shares sold
            transaction_fee: Transaction fee
            
        Returns:
            Realized P&L
        """
        sell_value = sell_price * quantity
        buy_value = avg_buy_price * quantity
        return sell_value - buy_value - transaction_fee
