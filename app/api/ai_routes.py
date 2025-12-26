"""
AI Assistant API routes
Provides AI-powered stock analysis and trading insights.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.stock import Stock
from app.api.schemas import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIChatRequest,
    AIChatResponse
)
from app.auth import get_current_user
from app.services.ai_assistant import get_ai_assistant
from app.services.paper_trading import PaperTradingService
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/analyze-stock", response_model=AIAnalysisResponse)
async def analyze_stock(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI analysis for a specific stock.
    
    Provides educational insights based on current stock data.
    Includes risk assessment and learning points.
    
    **Disclaimer**: This is not financial advice. AI suggestions are for
    educational purposes only. Always do your own research.
    """
    # Get stock data
    stock = db.query(Stock).filter(Stock.id == request.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock_data = stock.to_dict()
    
    # Get AI assistant
    ai_assistant = get_ai_assistant()
    
    # Get analysis
    result = await ai_assistant.get_stock_analysis(
        stock_data=stock_data,
        user_query=request.user_query
    )
    
    return result


@router.get("/portfolio-insights")
async def get_portfolio_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI insights on your current portfolio.
    
    Provides educational feedback on:
    - Portfolio diversification
    - Risk exposure
    - Learning opportunities
    - General market perspective
    
    **Disclaimer**: This is educational content, not investment advice.
    """
    # Get portfolio data
    portfolio_summary = PaperTradingService.get_portfolio_summary(db, current_user.id)
    
    if 'error' in portfolio_summary:
        raise HTTPException(status_code=400, detail=portfolio_summary['error'])
    
    # Get AI assistant
    ai_assistant = get_ai_assistant()
    
    # Get insights
    result = await ai_assistant.get_portfolio_insights(
        portfolio_data=portfolio_summary.get('holdings', []),
        total_value=portfolio_summary.get('total_portfolio_value', 0),
        pnl=portfolio_summary.get('pnl', {})
    )
    
    return result


@router.get("/market-overview")
async def get_market_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI overview of current market movements.
    
    Provides educational insights on:
    - Overall market sentiment
    - Sector trends
    - Learning points for traders
    - Risk considerations
    """
    from app.api.stock_routes import get_market_movers
    
    # Get market movers data
    try:
        # Get top gainers
        gainers_response = await get_market_movers(
            mover_type="gainers",
            limit=10,
            current_user=current_user,
            db=db
        )
        
        # Get top losers
        losers_response = await get_market_movers(
            mover_type="losers",
            limit=10,
            current_user=current_user,
            db=db
        )
        
        market_movers = {
            'top_gainers': gainers_response.get('stocks', []),
            'top_losers': losers_response.get('stocks', [])
        }
        
        # Get AI assistant
        ai_assistant = get_ai_assistant()
        
        # Get overview
        result = await ai_assistant.get_market_overview(market_movers)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating market overview: {str(e)}")


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI trading assistant.
    
    Ask questions about:
    - Stock market basics
    - Trading strategies (educational)
    - Market terminology
    - Risk management principles
    
    The AI will provide educational responses following ethical guidelines.
    
    **Important**: AI responses are for learning purposes only and should
    not be considered as financial advice.
    """
    # Get AI assistant
    ai_assistant = get_ai_assistant()
    
    # Add user context if requested
    context = request.context or {}
    
    # Optionally add user's portfolio data to context
    if context.get('include_portfolio', False):
        portfolio_summary = PaperTradingService.get_portfolio_summary(db, current_user.id)
        if 'error' not in portfolio_summary:
            context['portfolio'] = {
                'total_value': portfolio_summary.get('total_portfolio_value'),
                'pnl': portfolio_summary.get('pnl'),
                'num_positions': portfolio_summary.get('num_positions')
            }
    
    # Get AI response
    result = await ai_assistant.chat(
        user_message=request.message,
        context=context
    )
    
    return result


@router.get("/status")
async def get_ai_status():
    """
    Check if AI assistant is available and configured.
    """
    ai_assistant = get_ai_assistant()
    
    return {
        "available": ai_assistant.is_available,
        "model": "Google Gemini Pro" if ai_assistant.is_available else "Not configured",
        "message": "AI assistant is ready" if ai_assistant.is_available else "AI assistant is not available. Please configure API keys."
    }
