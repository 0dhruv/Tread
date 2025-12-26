"""
AI Trading Assistant Service
Integrates with Google Gemini (free tier) for intelligent trading suggestions.
Implements ethical AI principles with clear disclaimers.

AI Model Selection Justification:
1. Google Gemini (Primary): Free tier with 60 requests/minute
   - Pros: High quality, generous free tier, fast responses
   - Cons: Requires API key, rate limits
2. OpenAI GPT (Optional): Better quality but requires paid plan
3. Anthropic Claude (Optional): Strong reasoning but paid only

Ethics Implementation:
- No guaranteed returns promises
- Clear risk disclaimers
- Encouraging research over blind following
- Transparent about AI limitations
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available. AI features will be disabled.")

from app.config import settings

logger = logging.getLogger(__name__)


# System prompt emphasizing ethical AI principles
TRADING_ANALYST_SYSTEM_PROMPT = """
You are a Trading Analyst and Guide for the Indian stock market. Your role is to provide educational insights and suggestions based on market data, while strictly adhering to AI ethics principles.

CORE PRINCIPLES:
1. **No Guaranteed Returns**: Never promise or imply guaranteed profits or specific return percentages.
2. **Risk Disclosure**: Always mention market risks and potential for losses.
3. **Educational Focus**: Frame suggestions as learning opportunities, not definitive advice.
4. **Encourage Research**: Recommend users conduct their own research and due diligence.
5. **Transparency**: Be clear about AI limitations and uncertainty in predictions.
6. **No Pressure**: Avoid language that creates urgency or FOMO (Fear of Missing Out).

RESPONSE GUIDELINES:
- Start with appropriate disclaimers about market risks
- Use phrases like "based on current data", "historically", "may indicate"
- Avoid "will", "guaranteed", "certain", "definitely" when discussing future outcomes
- Suggest multiple perspectives and alternatives
- Emphasize diversification and risk management
- Reference fundamental and technical indicators when available

OUTPUT FORMAT:
- Clear, concise analysis
- Bullet points for readability
- Risk level assessment (Low/Medium/High)
- Timeframe considerations
- Always end with: "This is not financial advice. Please do your own research (DYOR) and consult with a certified financial advisor before making investment decisions."

Remember: You're an educational tool, not a financial advisor.
"""


class AITradingAssistant:
    """
    AI-powered trading assistant using Google Gemini.
    Provides ethical, educational market insights.
    """
    
    def __init__(self):
        """Initialize AI assistant with API configuration"""
        self.model = None
        self.is_available = False
        
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini library not available")
            return
        
        if not settings.GOOGLE_API_KEY:
            logger.warning("Google API key not configured. AI features disabled.")
            return
        
        try:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            # Initialize Gemini Pro model
            self.model = genai.GenerativeModel(
                'gemini-pro',
                generation_config={
                    'temperature': 0.7,  # Balanced creativity and consistency
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )
            
            self.is_available = True
            logger.info("AI Trading Assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.is_available = False
    
    def _format_stock_data(self, stock_data: Dict) -> str:
        """
        Format stock data for AI context.
        
        Args:
            stock_data: Dictionary with stock information
            
        Returns:
            Formatted string for AI prompt
        """
        return f"""
Stock: {stock_data.get('name', 'Unknown')} ({stock_data.get('symbol', 'N/A')})
Sector: {stock_data.get('sector', 'Unknown')}
Current Price: ₹{stock_data.get('current_price', 0):,.2f}
Market Cap: ₹{stock_data.get('market_cap', 0):,.0f} Cr
Recent Change: {stock_data.get('change_percent', 0):.2f}%
"""
    
    def _format_market_context(self, market_data: List[Dict]) -> str:
        """
        Format market overview data for AI context.
        
        Args:
            market_data: List of stock performance data
            
        Returns:
            Formatted market context string
        """
        gainers = [s for s in market_data if s.get('change_percent', 0) > 0]
        losers = [s for s in market_data if s.get('change_percent', 0) < 0]
        
        return f"""
Market Overview:
- Total Stocks Analyzed: {len(market_data)}
- Gainers: {len(gainers)}
- Losers: {len(losers)}
- Avg Change: {sum(s.get('change_percent', 0) for s in market_data) / len(market_data) if market_data else 0:.2f}%
"""
    
    async def get_stock_analysis(
        self,
        stock_data: Dict,
        user_query: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get AI analysis for a specific stock.
        
        Args:
            stock_data: Stock information and market data
            user_query: Optional specific user question
            
        Returns:
            Dictionary with analysis and metadata
        """
        if not self.is_available:
            return {
                'analysis': 'AI assistant is not available. Please configure API keys.',
                'status': 'unavailable'
            }
        
        try:
            # Build prompt
            stock_info = self._format_stock_data(stock_data)
            
            prompt = f"{TRADING_ANALYST_SYSTEM_PROMPT}\n\n"
            prompt += f"STOCK DATA:\n{stock_info}\n\n"
            
            if user_query:
                prompt += f"USER QUESTION:\n{user_query}\n\n"
            else:
                prompt += "Provide a brief analysis of this stock including key strengths, risks, and educational insights.\n\n"
            
            prompt += "Provide your analysis following the ethical guidelines and output format specified above."
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            return {
                'analysis': response.text,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'stock_symbol': stock_data.get('symbol', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error generating stock analysis: {e}")
            return {
                'analysis': f'Error generating analysis: {str(e)}',
                'status': 'error'
            }
    
    async def get_portfolio_insights(
        self,
        portfolio_data: List[Dict],
        total_value: float,
        pnl: Dict
    ) -> Dict[str, str]:
        """
        Get AI insights on user's portfolio.
        
        Args:
            portfolio_data: List of portfolio holdings
            total_value: Total portfolio value
            pnl: Profit/Loss data
            
        Returns:
            Dictionary with insights and recommendations
        """
        if not self.is_available:
            return {
                'insights': 'AI assistant is not available.',
                'status': 'unavailable'
            }
        
        try:
            # Build portfolio summary
            portfolio_summary = f"""
Portfolio Summary:
- Total Value: ₹{total_value:,.2f}
- Total P&L: ₹{pnl.get('total_pnl', 0):,.2f} ({pnl.get('pnl_percent', 0):.2f}%)
- Number of Holdings: {len(portfolio_data)}

Holdings:
"""
            for holding in portfolio_data[:10]:  # Limit to top 10
                portfolio_summary += f"- {holding.get('stock_name', 'Unknown')}: {holding.get('quantity', 0)} shares, "
                portfolio_summary += f"P&L: {holding.get('unrealized_pnl_percent', 0):.2f}%\n"
            
            prompt = f"{TRADING_ANALYST_SYSTEM_PROMPT}\n\n"
            prompt += f"PORTFOLIO DATA:\n{portfolio_summary}\n\n"
            prompt += """
Provide educational insights on this portfolio including:
1. Diversification assessment
2. Risk exposure considerations
3. Potential areas for learning and improvement
4. General market perspective

Remember to follow ethical guidelines and avoid specific buy/sell recommendations.
"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'insights': response.text,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio insights: {e}")
            return {
                'insights': f'Error generating insights: {str(e)}',
                'status': 'error'
            }
    
    async def get_market_overview(
        self,
        market_movers: Dict[str, List[Dict]]
    ) -> Dict[str, str]:
        """
        Get AI overview of market movements.
        
        Args:
            market_movers: Dictionary with gainers, losers, and active stocks
            
        Returns:
            Dictionary with market overview
        """
        if not self.is_available:
            return {
                'overview': 'AI assistant is not available.',
                'status': 'unavailable'
            }
        
        try:
            # Build market summary
            market_summary = "Market Movements Today:\n\n"
            
            if 'top_gainers' in market_movers:
                market_summary += "Top Gainers:\n"
                for stock in market_movers['top_gainers'][:5]:
                    market_summary += f"- {stock.get('name', 'Unknown')}: +{stock.get('change_percent', 0):.2f}%\n"
            
            market_summary += "\n"
            
            if 'top_losers' in market_movers:
                market_summary += "Top Losers:\n"
                for stock in market_movers['top_losers'][:5]:
                    market_summary += f"- {stock.get('name', 'Unknown')}: {stock.get('change_percent', 0):.2f}%\n"
            
            prompt = f"{TRADING_ANALYST_SYSTEM_PROMPT}\n\n"
            prompt += f"MARKET DATA:\n{market_summary}\n\n"
            prompt += """
Provide an educational overview of today's market movements including:
1. Overall market sentiment
2. Notable sector trends (if identifiable)
3. Learning points for traders
4. Risk considerations

Keep it concise and educational.
"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'overview': response.text,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating market overview: {e}")
            return {
                'overview': f'Error generating overview: {str(e)}',
                'status': 'error'
            }
    
    async def chat(self, user_message: str, context: Dict = None) -> Dict[str, str]:
        """
        General chat interface for user questions.
        
        Args:
            user_message: User's message/question
            context: Optional context (stocks, portfolio, etc.)
            
        Returns:
            Dictionary with AI response
        """
        if not self.is_available:
            return {
                'response': 'AI assistant is not available. Please configure Google API key in settings.',
                'status': 'unavailable'
            }
        
        try:
            prompt = f"{TRADING_ANALYST_SYSTEM_PROMPT}\n\n"
            
            if context:
                prompt += f"CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
            
            prompt += f"USER MESSAGE:\n{user_message}\n\n"
            prompt += "Provide a helpful, educational response following ethical guidelines."
            
            response = self.model.generate_content(prompt)
            
            return {
                'response': response.text,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI chat: {e}")
            return {
                'response': f'Error: {str(e)}',
                'status': 'error'
            }


# Global AI assistant instance
_ai_assistant = None


def get_ai_assistant() -> AITradingAssistant:
    """Get or create global AI assistant instance"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AITradingAssistant()
    return _ai_assistant
