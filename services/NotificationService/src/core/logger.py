from loguru import logger
import sys
import os

LOG_DIR = "../logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)
 
logger.add(
    f"{LOG_DIR}/app.log",
    rotation="10 MB",   
    retention="10 days",    
    compression="zip",      
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
)

logger.add(
    f"{LOG_DIR}/error.log",
    level="ERROR",
    rotation="5 MB",
    retention="15 days",
    compression="zip",
)

__all__ = ["logger"]