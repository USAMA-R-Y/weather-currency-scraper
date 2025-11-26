from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/weather_tracker.db"
    
    # Scraper Configuration
    SCRAPE_WINDOW_START: str = "02:00"
    SCRAPE_WINDOW_END: str = "05:00"
    SCRAPER_LOCATIONS: str = "Karachi,London,New York"
    CURRENCIES: str = "USD,EUR,GBP,PKR"
    
    # Scheduler Configuration
    TASK_TIMEZONE: str = "UTC"
    TASK_MAX_INSTANCES: int = 1
    TASK_MISFIRE_GRACE: int = 300  # 5 minutes
    
    # Git Configuration
    GIT_USER_NAME: Optional[str] = None
    GIT_USER_EMAIL: Optional[str] = None
    GIT_PUSH_ENABLED: bool = False
    
    # Security
    ADMIN_TOKEN: Optional[str] = None
    
    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL for SQLAlchemy."""
        return self.DATABASE_URL
    
    @property
    def scheduler_database_url(self) -> str:
        """Get the database URL for APScheduler (uses postgresql:// instead of postgresql+psycopg://)."""
        if self.DATABASE_URL.startswith("postgresql+"):
            return self.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
