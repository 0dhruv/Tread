"""
Paper Trading API routes
Handles buy/sell operations, portfolio management, and transaction history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.stock import Stock
from app.api.schemas import (
    TradeRequest,
    TransactionResponse,
    PortfolioSummary,
    TransactionHistory
)
from app.auth import get_current_user
from app.services.paper_trading import PaperTradingService

router = APIRouter(prefix="/trading", tags=["Paper Trading"])


@router.post("/buy", response_model=TransactionResponse)
async def buy_stock(
    trade: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a buy order for a stock.
    
    Deducts funds from paper balance and adds shares to portfolio.
    Transaction fee is automatically calculated and applied.
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.id == trade.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if not stock.is_active:
        raise HTTPException(status_code=400, detail="Stock is not active for trading")
    
    # Execute buy
    success, message, transaction = PaperTradingService.execute_buy(
        db=db,
        user_id=current_user.id,
        stock_id=trade.stock_id,
        quantity=trade.quantity,
        price=trade.price,
        notes=trade.notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return transaction


@router.post("/sell", response_model=TransactionResponse)
async def sell_stock(
    trade: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a sell order for a stock.
    
    Adds funds to paper balance and removes shares from portfolio.
    Calculates and returns realized P&L.
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.id == trade.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Execute sell
    success, message, transaction = PaperTradingService.execute_sell(
        db=db,
        user_id=current_user.id,
        stock_id=trade.stock_id,
        quantity=trade.quantity,
        price=trade.price,
        notes=trade.notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return transaction


@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's portfolio summary.
    
    Returns:
    - Cash balance
    - All holdings with current prices and P&L
    - Total portfolio value
    - Overall profit/loss
    """
    summary = PaperTradingService.get_portfolio_summary(db, current_user.id)
    
    if 'error' in summary:
        raise HTTPException(status_code=400, detail=summary['error'])
    
    return summary


@router.get("/transactions", response_model=TransactionHistory)
async def get_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for current user.
    
    Returns paginated list of all buy/sell transactions.
    """
    history = PaperTradingService.get_transaction_history(
        db, current_user.id, limit, offset
    )
    
    if 'error' in history:
        raise HTTPException(status_code=400, detail=history['error'])
    
    return history


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's paper trading balance.
    """
    return {
        "user_id": current_user.id,
        "cash_balance": round(current_user.paper_balance, 2),
        "initial_balance": round(current_user.initial_balance, 2)
    }


@router.post("/reset-portfolio")
async def reset_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset portfolio to initial state.
    
    WARNING: This will:
    - Clear all holdings
    - Clear all transaction history
    - Reset balance to initial value
    
    This action cannot be undone!
    """
    from app.models.portfolio import Portfolio
    from app.models.transaction import Transaction
    from app.config import settings
    
    # Delete all holdings
    db.query(Portfolio).filter(Portfolio.user_id == current_user.id).delete()
    
    # Delete all transactions
    db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
    
    # Reset balance
    current_user.paper_balance = settings.INITIAL_PORTFOLIO_VALUE
    current_user.initial_balance = settings.INITIAL_PORTFOLIO_VALUE
    
    db.commit()
    
    return {
        "message": "Portfolio reset successfully",
        "new_balance": current_user.paper_balance
    }
