# 📈 Indian Stock Market Trading Platform

A **high-performance FastAPI application** for Indian stock market analysis and paper trading, featuring AI-powered insights, real-time data, and a stunning modern UI.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

### 📊 **Data Collection**
- **7500+ Indian Stocks**: NSE and BSE listed companies
- **Free Data Source**: yfinance (Yahoo Finance) - no API key required
- **Real-time Prices**: Market capitalization and daily OHLC data
- **Historical Data**: Up to 365 days of price history
- **Concurrent Downloads**: High-performance parallel data collection

### 💾 **Data Storage**
- **PostgreSQL Database**: Scalable relational database
- **Optimized Indexes**: Fast querying for analytics and filtering
- **Time-Series Data**: Efficient historical price storage
- **Connection Pooling**: High-performance database connections

### 📈 **Analytics & Visualization**
- **Market Movers**: Top gainers and losers with customizable thresholds
- **Price Change Filters**: Find stocks moving 2%, 5%, 10%, 15%+
- **Sector Performance**: Aggregate analytics by industry sector
- **Interactive Charts**: Plotly-powered visualizations
- **Sortable Tables**: Filter and sort by any metric

### 💰 **Paper Trading**
- **Realistic Simulation**: Transaction fees (0.05%), balance checks
- **Portfolio Management**: Track positions, P&L, and performance
- **Buy/Sell Orders**: Execute trades with current market prices
- **Transaction History**: Complete audit trail of all trades
- **Position Limits**: Risk management with max position sizing

### 🤖 **AI-Assisted Suggestions**
- **Google Gemini Integration**: Free tier AI model
- **Ethical Guidelines**: Clear disclaimers, no guaranteed returns
- **Stock Analysis**: Educational insights on individual stocks
- **Portfolio Insights**: Diversification and risk assessment
- **Market Overview**: Daily market sentiment analysis
- **Interactive Chat**: Ask questions about trading and markets

### 🔐 **Security & Authentication**
- **JWT Tokens**: Secure authentication
- **Password Hashing**: bcrypt encryption
- **Protected Routes**: User-specific data access

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis (optional, for caching)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/stock-trading-platform.git
cd stock-trading-platform
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_trading

# Google Gemini API (Free tier)
# Get your key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-google-gemini-api-key

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

### 4. Initialize Database

```bash
# Start PostgreSQL service
# Then run:
python -c "from app.database import init_db; init_db()"
```

### 5. Collect Stock Data

```bash
# Collect data for 50 stocks with 365 days history
python scripts/collect_data.py --stocks 50 --days 365

# Or collect all stocks (takes longer)
python scripts/collect_data.py --days 365
```

### 6. Run Application

```bash
# Development mode
uvicorn main:app --reload

# Production mode
python main.py
```

Visit **http://localhost:8000** for the application and **http://localhost:8000/docs** for API documentation.

## 📚 API Documentation

### Authentication

```bash
# Register new user
POST /api/auth/register
{
  "email": "user@example.com",
  "username": "trader1",
  "password": "securepassword",
  "full_name": "John Doe"
}

# Login
POST /api/auth/login
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

### Stocks & Market Data

```bash
# Get all stocks (paginated)
GET /api/stocks/?page=1&page_size=50&sector=Technology

# Get stock details
GET /api/stocks/{stock_id}

# Get historical data
GET /api/stocks/{stock_id}/history?days=30

# Get market movers
GET /api/stocks/market/movers?mover_type=gainers&limit=20

# Find stocks by price change
GET /api/stocks/analytics/price-change?change_percent=5&tolerance=0.5
```

### Paper Trading

```bash
# Buy stock
POST /api/trading/buy
{
  "stock_id": 1,
  "quantity": 10,
  "price": 2500.50
}

# Sell stock
POST /api/trading/sell
{
  "stock_id": 1,
  "quantity": 5,
  "price": 2600.75
}

# Get portfolio
GET /api/trading/portfolio

# Get transaction history
GET /api/trading/transactions?limit=50
```

### AI Assistant

```bash
# Get stock analysis
POST /api/ai/analyze-stock
{
  "stock_id": 1,
  "user_query": "What are the key risks?"
}

# Get portfolio insights
GET /api/ai/portfolio-insights

# Chat with AI
POST /api/ai/chat
{
  "message": "Explain diversification strategy"
}
```

## 🏗️ Architecture

```
stock-trading-platform/
├── app/
│   ├── api/                  # FastAPI routes
│   │   ├── auth_routes.py    # Authentication endpoints
│   │   ├── stock_routes.py   # Stock & market data endpoints
│   │   ├── trading_routes.py # Paper trading endpoints
│   │   ├── ai_routes.py      # AI assistant endpoints
│   │   └── schemas.py        # Pydantic schemas
│   ├── models/               # SQLAlchemy models
│   │   ├── stock.py
│   │   ├── market_data.py
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   └── transaction.py
│   ├── services/             # Business logic
│   │   ├── market_data_collector.py  # Data collection
│   │   ├── ai_assistant.py           # AI integration
│   │   └── paper_trading.py          # Trading logic
│   ├── config.py             # Configuration
│   ├── database.py           # Database setup
│   └── auth.py               # Authentication
├── static/                   # Frontend files
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── scripts/
│   └── collect_data.py       # Data collection script
├── main.py                   # Application entry point
├── requirements.txt
└── .env.example
```

## 📊 Database Schema

### Stocks Table
- `id`: Primary key
- `symbol`: Stock ticker (e.g., RELIANCE.NS)
- `name`: Company name
- `exchange`: NSE/BSE
- `sector`, `industry`: Classification
- `market_cap`, `current_price`: Market data

### Market Data Table
- `id`: Primary key
- `stock_id`: Foreign key to Stocks
- `date`: Trading date
- `open`, `high`, `low`, `close`: OHLC prices
- `volume`: Trading volume
- `change_percent`: Daily percentage change

### Users Table
- Authentication and profile
- `paper_balance`: Current cash balance
- `initial_balance`: Starting balance for P&L

### Portfolio Table
- User stock holdings
- Average buy price, quantity
- Real-time P&L calculation

### Transactions Table
- Complete trade history
- Buy/sell with fees and realized P&L

## 🎨 Frontend Features

- **Modern Dark UI**: Glassmorphism with vibrant gradients
- **Responsive Design**: Mobile-friendly layout
- **Real-time Updates**: Live portfolio and market data
- **Interactive Charts**: Plotly visualizations
- **AI Chat Interface**: Conversational trading assistant
- **Quick Trade Modal**: Fast execution interface

## 🔍 Data Source Selection

### Why yfinance?

**Pros:**
- ✅ **Free**: No API key required
- ✅ **Comprehensive**: 7500+ Indian stocks (NSE/BSE)
- ✅ **Reliable**: Maintained open-source library
- ✅ **Rich Data**: OHLC, volume, market cap, fundamentals
- ✅ **Historical Data**: Years of price history

**Cons:**
- ⚠️ ~15 minute delay for real-time data
- ⚠️ Unofficial API (wraps Yahoo Finance)
- ⚠️ Rate limits on heavy usage

**Alternatives Considered:**
- NSE India API (requires paid subscription)
- Alpha Vantage (limited free tier)
- Breeze API (requires broker account)

## 🤖 AI Model Selection

### Why Google Gemini?

**Pros:**
- ✅ **Free Tier**: 60 requests/minute
- ✅ **High Quality**: Advanced language model
- ✅ **Fast**: Low latency responses
- ✅ **Easy Integration**: Official Python SDK

**Alternatives:**
- OpenAI GPT-4 (paid, higher quality)
- Anthropic Claude (paid, strong reasoning)
- Open-source LLMs (self-hosted, resource-intensive)

### Ethical AI Implementation

Our AI assistant follows strict ethical guidelines:

1. **No Guaranteed Returns**: Avoids promises of specific profits
2. **Risk Disclosure**: Always mentions market risks
3. **Educational Focus**: Frames as learning, not advice
4. **Encourage Research**: Promotes due diligence (DYOR)
5. **Transparency**: Clear about AI limitations
6. **Safe Language**: No FOMO or pressure tactics

**Every AI response includes:**
> "This is not financial advice. Please do your own research (DYOR) and consult with a certified financial advisor before making investment decisions."

## 🚀 Performance Optimizations

- **Database Indexes**: Optimized for common queries
- **Connection Pooling**: Reuse database connections
- **Concurrent Downloads**: Parallel stock data fetching
- **Caching**: Redis for frequently accessed data
- **Async API**: FastAPI's async capabilities

## 📝 Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `GOOGLE_API_KEY` | Google Gemini API key | Required for AI |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `INITIAL_PORTFOLIO_VALUE` | Starting cash for new users | `1000000` (10L) |
| `TRANSACTION_FEE_PERCENT` | Trading fee percentage | `0.0005` (0.05%) |
| `MAX_POSITION_SIZE` | Max % of portfolio per stock | `0.2` (20%) |
| `HISTORICAL_DATA_DAYS` | Days of historical data | `365` |

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## ⚠️ Disclaimer

**This platform is for educational and simulation purposes only.**

- Not financial advice
- Paper trading only (no real money)
- Past performance doesn't guarantee future results
- Consult certified financial advisors before investing

## 🙏 Acknowledgments

- **yfinance**: Stock data provider
- **FastAPI**: Web framework
- **Google Gemini**: AI model
- **Plotly**: Visualization library
- **PostgreSQL**: Database system

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, PostgreSQL, and Google Gemini
