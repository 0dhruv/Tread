"""
User model for authentication and paper trading accounts.
Implements secure password hashing and JWT token support.
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from passlib.context import CryptContext

from app.database import Base

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User authentication and profile table.
    Each user has a paper trading portfolio.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email (unique identifier)"
    )
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Display username"
    )
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(100), comment="User's full name")
    
    # Account Status
    is_active = Column(Boolean, default=True, comment="Account active status")
    is_verified = Column(Boolean, default=False, comment="Email verified")
    
    # Paper Trading Balance
    paper_balance = Column(
        Float,
        default=1000000.0,
        nullable=False,
        comment="Paper trading balance in INR (default: 10 Lakhs)"
    )
    initial_balance = Column(
        Float,
        default=1000000.0,
        nullable=False,
        comment="Initial balance for P&L calculation"
    )
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login = Column(DateTime, comment="Last login timestamp")
    
    # Relationships
    portfolios = relationship(
        "Portfolio",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Transaction.created_at.desc()"
    )
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"
    
    def to_dict(self, include_sensitive=False):
        """Convert model to dictionary for API responses"""
        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "paper_balance": round(self.paper_balance, 2),
            "initial_balance": round(self.initial_balance, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        
        return data
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify password against hashed password"""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a plain password"""
        return pwd_context.hash(plain_password)
    
    def update_password(self, new_password: str):
        """Update user password with new hashed value"""
        self.hashed_password = self.hash_password(new_password)
    
    def calculate_total_portfolio_value(self) -> float:
        """
        Calculate total portfolio value including cash balance.
        Returns: total_value (cash + holdings)
        """
        holdings_value = sum(
            portfolio.quantity * portfolio.current_price
            for portfolio in self.portfolios
            if portfolio.quantity > 0
        )
        return self.paper_balance + holdings_value
    
    def calculate_pnl(self) -> dict:
        """
        Calculate profit and loss.
        Returns: dict with total_pnl, pnl_percent, current_value
        """
        current_value = self.calculate_total_portfolio_value()
        total_pnl = current_value - self.initial_balance
        pnl_percent = (total_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        
        return {
            "total_pnl": round(total_pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "current_value": round(current_value, 2),
            "initial_value": round(self.initial_balance, 2)
        }
