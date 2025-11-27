from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import setup_logging

# Setup logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Automated Weather Tracker",
    description="Automated weather and currency data scraper with FastAPI and APScheduler",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
try:
    from app.modules.weather.router import router as weather_router
    app.include_router(weather_router, prefix="/api/weather", tags=["weather"])
except ImportError:
    pass

try:
    from app.modules.currency.router import router as currency_router
    app.include_router(currency_router, prefix="/api/currency", tags=["currency"])
except ImportError:
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Automated Weather Tracker API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    from app.core.logger import logger
    logger.info("Starting Automated Weather Tracker...")
    
    # Initialize scheduler
    try:
        from jobs.scheduler import init_scheduler
        init_scheduler()
        logger.info("Scheduler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    from app.core.logger import logger
    logger.info("Shutting down Automated Weather Tracker...")
