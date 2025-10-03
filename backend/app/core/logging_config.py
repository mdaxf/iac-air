import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from functools import wraps
import time
from contextlib import contextmanager
from datetime import datetime
from .config import settings

class LoggerSetup:
    """Configure and setup logging for the application"""

    def __init__(self):
        self.log_dir = Path(settings.LOG_DIR)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_loggers()

    def _get_file_handler(self, filename: str, level: int) -> logging.handlers.TimedRotatingFileHandler:
        """Create a file handler with rotation"""
        filepath = self.log_dir / filename

        if settings.LOG_ROTATION == "daily":
            handler = logging.handlers.TimedRotatingFileHandler(
                filepath,
                when='D',
                interval=1,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
        elif settings.LOG_ROTATION == "hourly":
            handler = logging.handlers.TimedRotatingFileHandler(
                filepath,
                when='H',
                interval=1,
                backupCount=settings.LOG_BACKUP_COUNT * 24,
                encoding='utf-8'
            )
        else:  # size-based rotation
            max_bytes = self._parse_size(settings.LOG_MAX_FILE_SIZE)
            handler = logging.handlers.RotatingFileHandler(
                filepath,
                maxBytes=max_bytes,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )

        handler.setLevel(level)
        formatter = logging.Formatter(
            settings.LOG_FORMAT,
            datefmt=settings.LOG_DATE_FORMAT
        )
        handler.setFormatter(formatter)
        return handler

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def _setup_loggers(self):
        """Setup different loggers for different purposes"""
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handlers for different log levels
        self._setup_level_loggers()
        self._setup_special_loggers()

    def _setup_level_loggers(self):
        """Setup loggers for different levels"""
        # Main application log (all levels)
        app_logger = logging.getLogger('app')
        app_handler = self._get_file_handler('app.log', logging.DEBUG)
        app_logger.addHandler(app_handler)
        app_logger.propagate = False

        # Error log
        error_logger = logging.getLogger('error')
        error_handler = self._get_file_handler('error.log', logging.ERROR)
        error_logger.addHandler(error_handler)
        error_logger.propagate = False

        # Warning log
        warning_logger = logging.getLogger('warning')
        warning_handler = self._get_file_handler('warning.log', logging.WARNING)
        warning_logger.addHandler(warning_handler)
        warning_logger.propagate = False

        # Info log
        info_logger = logging.getLogger('info')
        info_handler = self._get_file_handler('info.log', logging.INFO)
        info_logger.addHandler(info_handler)
        info_logger.propagate = False

        # Debug log
        debug_logger = logging.getLogger('debug')
        debug_handler = self._get_file_handler('debug.log', logging.DEBUG)
        debug_logger.addHandler(debug_handler)
        debug_logger.propagate = False

    def _setup_special_loggers(self):
        """Setup special purpose loggers"""
        # Performance log
        perf_logger = logging.getLogger('performance')
        perf_handler = self._get_file_handler('performance.log', logging.INFO)
        perf_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt=settings.LOG_DATE_FORMAT
        )
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False

        # Security log
        security_logger = logging.getLogger('security')
        security_handler = self._get_file_handler('security.log', logging.INFO)
        security_logger.addHandler(security_handler)
        security_logger.propagate = False

        # API access log
        access_logger = logging.getLogger('access')
        access_handler = self._get_file_handler('access.log', logging.INFO)
        access_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt=settings.LOG_DATE_FORMAT
        )
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False


# Global logger setup
logger_setup = LoggerSetup()

# Logger instances
app_logger = logging.getLogger('app')
error_logger = logging.getLogger('error')
warning_logger = logging.getLogger('warning')
info_logger = logging.getLogger('info')
debug_logger = logging.getLogger('debug')
performance_logger = logging.getLogger('performance')
security_logger = logging.getLogger('security')
access_logger = logging.getLogger('access')


class Logger:
    """Enhanced logger with performance monitoring"""

    @staticmethod
    def debug(message: str, **kwargs):
        debug_logger.debug(message, extra=kwargs)

    @staticmethod
    def info(message: str, **kwargs):
        info_logger.info(message, extra=kwargs)
        app_logger.info(message, extra=kwargs)
        debug_logger.debug(message, extra=kwargs)

    @staticmethod
    def warning(message: str, **kwargs):
        warning_logger.warning(message, extra=kwargs)
        app_logger.warning(message, extra=kwargs)
        debug_logger.debug(message, extra=kwargs)

    @staticmethod
    def error(message: str, **kwargs):
        error_logger.error(message, extra=kwargs)
        app_logger.error(message, extra=kwargs)
        debug_logger.debug(message, extra=kwargs)

    @staticmethod
    def critical(message: str, **kwargs):
        error_logger.critical(message, extra=kwargs)
        app_logger.critical(message, extra=kwargs)
        debug_logger.debug(message, extra=kwargs)

    @staticmethod
    def performance(func_name: str, duration: float, **kwargs):
        performance_logger.info(
            f"PERF: {func_name} - Duration: {duration:.3f}s",
            extra={'function': func_name, 'duration': duration, **kwargs}
        )

    @staticmethod
    def security(message: str, **kwargs):
        security_logger.info(message, extra=kwargs)

    @staticmethod
    def access(message: str, **kwargs):
        access_logger.info(message, extra=kwargs)


def log_method_calls(func):
    """Decorator to log method entry/exit and performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"

        # Log method entry
        Logger.debug(f"ENTER: {func_name}")

        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            # Log method exit
            Logger.debug(f"EXIT: {func_name} - Duration: {duration:.3f}s")

            # Log performance if above threshold
            if duration > settings.PERFORMANCE_LOG_THRESHOLD:
                Logger.performance(func_name, duration)

            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            Logger.error(f"ERROR in {func_name}: {str(e)} - Duration: {duration:.3f}s")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"

        # Log method entry
        Logger.debug(f"ENTER: {func_name}")

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            # Log method exit
            Logger.debug(f"EXIT: {func_name} - Duration: {duration:.3f}s")

            # Log performance if above threshold
            if duration > settings.PERFORMANCE_LOG_THRESHOLD:
                Logger.performance(func_name, duration)

            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            Logger.error(f"ERROR in {func_name}: {str(e)} - Duration: {duration:.3f}s")
            raise

    # Return appropriate wrapper based on function type
    if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
        return async_wrapper
    else:
        return sync_wrapper


@contextmanager
def log_performance(operation_name: str):
    """Context manager for logging performance of code blocks"""
    Logger.debug(f"START: {operation_name}")
    start_time = time.time()
    try:
        yield
        end_time = time.time()
        duration = end_time - start_time
        Logger.debug(f"END: {operation_name} - Duration: {duration:.3f}s")

        if duration > settings.PERFORMANCE_LOG_THRESHOLD:
            Logger.performance(operation_name, duration)
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        Logger.error(f"ERROR in {operation_name}: {str(e)} - Duration: {duration:.3f}s")
        raise


# Initialize logging on import
logger_setup