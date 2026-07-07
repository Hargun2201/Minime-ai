# logging_config.py

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Sets up application-wide logger.
    Configures a RotatingFileHandler to write log events to logs/app.log
    and also logs to standard console output.
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Set up root logger configuration
    root_logger = logging.getLogger()
    
    # Do not add handlers if they are already initialized (prevents double logging in multiple modules)
    if root_logger.hasHandlers():
        return root_logger

    root_logger.setLevel(logging.DEBUG)

    # Formatter for structured logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. File Handler (Rotating, max 5MB, keep 3 backup logs)
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logging.info("Logging successfully initialized. Output directed to logs/app.log")
    except IOError as e:
        logging.error(f"Failed to initialize file logger: {e}")
        # Standard fallback to console remains active
        
    return root_logger
