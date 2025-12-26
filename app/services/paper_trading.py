"""
Paper Trading Service
Implements buy/sell operations, position management, and P&L tracking.
Simulates realistic trading with transaction fees and balance checks.
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.stock import Stock
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction, TransactionType
from app.config import settings

logger = logging.getLogger(__name__)


class PaperTradingService:
    """
    Service for executing paper trading operations.
    Handles buy/sell transactions with realistic constraints.
    """
    
    @staticmethod
    def calculate_total_cost(
        quantity: int,
        price: float,
        transaction_type: TransactionType
    ) -> Tuple[float, float, float]:
        """
        Calculate total cost including transaction fees.
        
        Args:
            quantity: Number of shares
            price: Price per share
            transaction_type: BUY or SELL
            
        Returns:
            Tuple of (total_value, transaction_fee, net_amount)
        """
        total_value = quantity * price
        transaction_fee = total_value * settings.TRANSACTION_FEE_PERCENT
        
        if transaction_type == TransactionType.BUY:
            # For buy: user pays total + fee
            net_amount = total_value + transaction_fee
        else:
            # For sell: user receives total - fee
            net_amount = total_value - transaction_fee
        
        return (total_value, transaction_fee, net_amount)
    
    @staticmethod
    def can_buy(
        user: User,
        quantity: int,
        price: float
    ) -> Tuple[bool, str]:
        """
        Check if user can afford to buy shares.
        
        Args:
            user: User instance
            quantity: Number of shares to buy
            price: Price per share
            
        Returns:
            Tuple of (can_buy, error_message)
        """
        total_value, transaction_fee, net_amount = PaperTradingService.calculate_total_cost(
            quantity, price, TransactionType.BUY
        )
        
        if net_amount > user.paper_balance:
            return (False, f"Insufficient balance. Required: ₹{net_amount:,.2f}, Available: ₹{user.paper_balance:,.2f}")
        
        # Check position size limit
        portfolio_value = user.calculate_total_portfolio_value()
        if portfolio_value > 0:
            position_percent = total_value / portfolio_value
            if position_percent > settings.MAX_POSITION_SIZE:
                return (False, f"Position size exceeds {settings.MAX_POSITION_SIZE*100}% limit")
        
        return (True, "")
    
    @staticmethod
    def execute_buy(
        db: Session,
        user_id: int,
        stock_id: int,
        quantity: int,
        price: float,
        notes: str = None
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Execute a buy transaction.
        
        Args:
            db: Database session
            user_id: User ID
            stock_id: Stock ID
            quantity: Number of shares
            price: Buy price per share
            notes: Optional transaction notes
            
        Returns:
            Tuple of (success, message, transaction)
        """
        try:
            # Get user and stock
            user = db.query(User).filter(User.id == user_id).first()
            stock = db.query(Stock).filter(Stock.id == stock_id).first()
            
            if not user or not stock:
                return (False, "User or stock not found", None)
            
            # Check if can buy
            can_buy, error_msg = PaperTradingService.can_buy(user, quantity, price)
            if not can_buy:
                return (False, error_msg, None)
            
            # Calculate costs
            total_value, transaction_fee, net_amount = PaperTradingService.calculate_total_cost(
                quantity, price, TransactionType.BUY
            )
            
            # Deduct from balance
            user.paper_balance -= net_amount
            
            # Update or create portfolio position
            portfolio = db.query(Portfolio).filter(
                and_(
                    Portfolio.user_id == user_id,
                    Portfolio.stock_id == stock_id
                )
            ).first()
            
            if portfolio:
                portfolio.add_shares(quantity, price)
            else:
                portfolio = Portfolio(
                    user_id=user_id,
                    stock_id=stock_id,
                    quantity=quantity,
                    average_buy_price=price,
                    current_price=price
                )
                portfolio.update_metrics(price)
                db.add(portfolio)
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                stock_id=stock_id,
                transaction_type=TransactionType.BUY,
                quantity=quantity,
                price=price,
                total_value=total_value,
                transaction_fee=transaction_fee,
                net_amount=net_amount,
                balance_after=user.paper_balance,
                notes=notes
            )
            db.add(transaction)
            
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"User {user_id} bought {quantity} shares of {stock.symbol} at ₹{price}")
            
            return (True, "Buy order executed successfully", transaction)
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            db.rollback()
            return (False, f"Error: {str(e)}", None)
    
    @staticmethod
    def execute_sell(
        db: Session,
        user_id: int,
        stock_id: int,
        quantity: int,
        price: float,
        notes: str = None
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Execute a sell transaction.
        
        Args:
            db: Database session
            user_id: User ID
            stock_id: Stock ID
            quantity: Number of shares
            price: Sell price per share
            notes: Optional transaction notes
            
        Returns:
            Tuple of (success, message, transaction)
        """
        try:
            # Get user, stock, and portfolio
            user = db.query(User).filter(User.id == user_id).first()
            stock = db.query(Stock).filter(Stock.id == stock_id).first()
            portfolio = db.query(Portfolio).filter(
                and_(
                    Portfolio.user_id == user_id,
                    Portfolio.stock_id == stock_id
                )
            ).first()
            
            if not user or not stock:
                return (False, "User or stock not found", None)
            
            if not portfolio or portfolio.quantity < quantity:
                available = portfolio.quantity if portfolio else 0
                return (False, f"Insufficient shares. Available: {available}, Requested: {quantity}", None)
            
            # Calculate proceeds
            total_value, transaction_fee, net_amount = PaperTradingService.calculate_total_cost(
                quantity, price, TransactionType.SELL
            )
            
            # Calculate realized P&L
            realized_pnl = Transaction.calculate_realized_pnl(
                price,
                portfolio.average_buy_price,
                quantity,
                transaction_fee
            )
            
            # Add to balance
            user.paper_balance += net_amount
            
            # Update portfolio
            portfolio.remove_shares(quantity)
            portfolio.update_metrics(price)
            
            # If no shares left, can delete portfolio entry or keep it at 0
            # We'll keep it for history
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                stock_id=stock_id,
                transaction_type=TransactionType.SELL,
                quantity=quantity,
                price=price,
                total_value=total_value,
                transaction_fee=transaction_fee,
                net_amount=net_amount,
                realized_pnl=realized_pnl,
                average_buy_price=portfolio.average_buy_price,
                balance_after=user.paper_balance,
                notes=notes
            )
            db.add(transaction)
            
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"User {user_id} sold {quantity} shares of {stock.symbol} at ₹{price}, P&L: ₹{realized_pnl:,.2f}")
            
            return (True, f"Sell order executed. P&L: ₹{realized_pnl:,.2f}", transaction)
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            db.rollback()
            return (False, f"Error: {str(e)}", None)
    
    @staticmethod
    def get_portfolio_summary(db: Session, user_id: int) -> Dict:
        """
        Get comprehensive portfolio summary.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with portfolio summary
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            portfolios = db.query(Portfolio).filter(
                and_(
                    Portfolio.user_id == user_id,
                    Portfolio.quantity > 0
                )
            ).all()
            
            holdings = []
            total_invested = 0
            total_current = 0
            
            for portfolio in portfolios:
                portfolio.update_metrics()  # Refresh with latest prices
                holdings.append(portfolio.to_dict(include_stock_details=True))
                total_invested += portfolio.invested_value or 0
                total_current += portfolio.current_value or 0
            
            pnl = user.calculate_pnl()
            
            return {
                'user_id': user_id,
                'cash_balance': round(user.paper_balance, 2),
                'invested_value': round(total_invested, 2),
                'current_value': round(total_current, 2),
                'total_portfolio_value': round(user.calculate_total_portfolio_value(), 2),
                'holdings': holdings,
                'pnl': pnl,
                'num_positions': len(holdings)
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_transaction_history(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Get user's transaction history.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Number of records to return
            offset: Pagination offset
            
        Returns:
            Dictionary with transaction history
        """
        try:
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(
                Transaction.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            total_count = db.query(Transaction).filter(
                Transaction.user_id == user_id
            ).count()
            
            return {
                'transactions': [t.to_dict(include_stock_details=True) for t in transactions],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return {'error': str(e)}
