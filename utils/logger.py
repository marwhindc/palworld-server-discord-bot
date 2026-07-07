import logging
import sys

def setup_logger(name: str = "palworld_bot", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a logger instance with a standardized output format."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already initialized
    if logger.handlers:
        return logger

    logger.setLevel(level)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Output to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Export standard logger
bot_logger = setup_logger()
