import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with full timestamp for each run
    log_filename = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler (stdout)
            logging.StreamHandler(sys.stdout),
            # File handler (separate file for each run)
            logging.FileHandler(log_filename, mode="w", encoding="utf-8")
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_filename}")
    
    return logger


# Initialize logger when module is imported
logger = setup_logging()
