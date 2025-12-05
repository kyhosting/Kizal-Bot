import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "bot", log_file: str = None) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = os.path.join("logs", log_file)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("pyrogram.session").setLevel(logging.ERROR)

    return logger


class BotLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._main_logger = setup_logger("bot", "bot.log")
            cls._error_logger = setup_logger("errors", "errors.log")
            cls._access_logger = setup_logger("access", "access.log")
        return cls._instance
    
    def info(self, message: str):
        self._main_logger.info(message)
    
    def error(self, message: str, exc_info: bool = False):
        self._error_logger.error(message, exc_info=exc_info)
        self._main_logger.error(message)
    
    def warning(self, message: str):
        self._main_logger.warning(message)
    
    def debug(self, message: str):
        self._main_logger.debug(message)
    
    def access(self, user_id: int, action: str, details: str = ""):
        self._access_logger.info(f"User {user_id} - {action} - {details}")
    
    def critical(self, message: str, exc_info: bool = True):
        self._error_logger.critical(message, exc_info=exc_info)
        self._main_logger.critical(message)


bot_logger = BotLogger()
