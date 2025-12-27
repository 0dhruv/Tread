"""
Main FastAPI application entry point.
Configures API routes, middleware, and startup/shutdown events.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.database import init_db, get_db_health
from app.api import auth_routes, stock_routes, trading_routes, ai_routes, realtime_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting FastAPI application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Check database health
    if not get_db_health():
        logger.warning("Database health check failed")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cleanup resources
    from app.services.market_data_collector import get_collector
    collector = get_collector()
    collector.shutdown()
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Indian Stock Market Trading Platform",
    description="""
    High-performance FastAPI application for Indian stock market analysis and paper trading.
    
    ## Features
    
    * 📊 **Real-time Market Data**: Access to 7500+ Indian stocks (NSE/BSE)
    * 📈 **Analytics Dashboard**: Track stocks by price movements (2%, 5%, 10%, 15%, etc.)
    * 💰 **Paper Trading**: Simulate trading with realistic transaction fees
    * 🤖 **AI Assistant**: Get intelligent, ethical trading insights powered by Google Gemini
    * 📱 **RESTful API**: Complete API for integration with any frontend
    
    ## Data Sources
    
    - **Primary**: yfinance (Yahoo Finance) - Free, reliable, 7500+ Indian stocks
    - **Features**: Historical data, market cap, sector information, real-time prices
    
    ## AI Ethics
    
    Our AI assistant follows strict ethical guidelines:
    - No guaranteed returns promises
    - Clear risk disclaimers
    - Educational focus
    - Transparent about limitations
    
    **Disclaimer**: This platform is for educational and simulation purposes only.
    Not financial advice. Always conduct your own research and consult with certified
    financial advisors before making investment decisions.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Indian Stock Trading Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_healthy = get_db_health()
    
    from app.services.ai_assistant import get_ai_assistant
    ai_assistant = get_ai_assistant()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "ai_assistant": "available" if ai_assistant.is_available else "unavailable",
        "timestamp": "2025-12-26T18:00:23+05:30"
    }


# Include API routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(stock_routes.router, prefix="/api")
app.include_router(trading_routes.router, prefix="/api")
app.include_router(ai_routes.router, prefix="/api")
app.include_router(realtime_routes.router, prefix="/api")


# Mount static files for frontend (if exists)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found. Skipping static files mounting.")


# Admin/utility endpoints
@app.post("/api/admin/collect-data", tags=["Admin"])
async def trigger_data_collection():
    """
    Trigger manual data collection for all stocks.
    
    This endpoint initiates the market data collector to fetch
    latest stock information and historical prices.
    
    **Note**: This is a long-running operation.
    """
    from app.services.market_data_collector import get_collector
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    collector = get_collector()
    
    # Run collection in background
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(collector.collect_all_stocks)
    
    return {
        "message": "Data collection started",
        "status": "running",
        "info": "This may take several minutes. Check logs for progress."
    }


@app.post("/api/admin/update-prices", tags=["Admin"])
async def trigger_price_update():
    """
    Update latest prices for all active stocks.
    
    Faster than full data collection - only updates current prices.
    """
    from app.services.market_data_collector import get_collector
    
    collector = get_collector()
    updated = collector.update_latest_prices()
    
    return {
        "message": "Price update complete",
        "stocks_updated": updated
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
