# app/core/logging_config.py
import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """Setup application logging configuration"""
    
    # Create logs directory
    if settings.LOG_DIR is not None:
        log_dir = Path(settings.LOG_DIR)
    else:
        log_dir = Path("logs")
    
    log_dir.mkdir(exist_ok=True)
    
    # Set log level based on environment
    if log_level is None:
        if settings.LOG_LEVEL is not None:
            log_level = settings.LOG_LEVEL.upper()
        else:
            log_level = "DEBUG" if settings.ENVIRONMENT == "development" else "INFO"
    
    # Get current date for log file naming
    today = datetime.now().strftime("%Y-%m-%d")
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": f"logs/qis_debug_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10
            },
            "info_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": f"logs/qis_info_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 30
            },
            "warning_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": f"logs/qis_warning_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 30
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": f"logs/qis_error_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 30
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "json",
                "filename": f"logs/qis_security_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 90  # Keep security logs longer
            },
            "api_debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": f"logs/qis_api_debug_{today}.log",
                "maxBytes": 20971520,  # 20MB for API debug (more verbose)
                "backupCount": 7
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "debug_file", "info_file", "warning_file", "error_file"]
            },
            "app": {  # Main app logger
                "level": "DEBUG",
                "handlers": ["console", "debug_file", "info_file", "warning_file", "error_file"],
                "propagate": False
            },
            "app.api": {  # API-specific debug logger
                "level": "DEBUG",
                "handlers": ["console", "api_debug_file", "debug_file"],
                "propagate": False
            },
            "app.info": {
                "level": "INFO",
                "handlers": ["console", "info_file"],
                "propagate": False
            },
            "app.debug": {
                "level": "DEBUG",
                "handlers": ["console", "debug_file"],
                "propagate": False
            },
            "app.security": {
                "level": log_level,
                "handlers": ["console", "security_file", "info_file"],
                "propagate": False
            },
            "app.errors": {
                "level": "ERROR",
                "handlers": ["console", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": log_level,
                "handlers": ["console", "info_file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": log_level,
                "handlers": ["debug_file"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)


# Security-specific logging utilities
class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger("app.security")
            
    def authentication_success(self, user_id: str, ip_address: str):
        self.logger.info(f"Authentication successful - User: {user_id}, IP: {ip_address}")
        self.logger.debug(f"Authentication successful - User: {user_id}, IP: {ip_address}")
    
    def authentication_failure(self, username: str, ip_address: str, reason: str = ""):
        self.logger.warning(f"Authentication failed - Username: {username}, IP: {ip_address}, Reason: {reason}")
        self.logger.info(f"Authentication failed - Username: {username}, IP: {ip_address}, Reason: {reason}")
        self.logger.debug(f"Authentication failed - Username: {username}, IP: {ip_address}, Reason: {reason}")
    
    def unauthorized_access(self, user_id: str, resource: str, ip_address: str):
        self.logger.warning(f"Unauthorized access attempt - User: {user_id}, Resource: {resource}, IP: {ip_address}")
        self.logger.info(f"Unauthorized access attempt - User: {user_id}, Resource: {resource}, IP: {ip_address}")
        self.logger.debug(f"Unauthorized access attempt - User: {user_id}, Resource: {resource}, IP: {ip_address}")
    
    def api_key_used(self, key_id: str, ip_address: str, endpoint: str):
        self.logger.info(f"API key used - Key ID: {key_id}, IP: {ip_address}, Endpoint: {endpoint}")
        self.logger.debug(f"API key details - Key ID: {key_id}, IP: {ip_address}, Endpoint: {endpoint}")
    
    def file_access(self, user_id: str, file_path: str, ip_address: str, action: str):
        self.logger.info(f"File access - User: {user_id}, File: {file_path}, IP: {ip_address}, Action: {action}")
        self.logger.debug(f"File access details - User: {user_id}, File: {file_path}, IP: {ip_address}, Action: {action}")
    
    def suspicious_activity(self, user_id: str, activity: str, ip_address: str):
        self.logger.error(f"Suspicious activity detected - User: {user_id}, Activity: {activity}, IP: {ip_address}")
        self.logger.info(f"Suspicious activity details - User: {user_id}, Activity: {activity}, IP: {ip_address}")
        self.logger.debug(f"Suspicious activity details - User: {user_id}, Activity: {activity}, IP: {ip_address}")


# Application-specific logger instances
app_logger = get_logger("app")
api_logger = get_logger("app.api")  # Dedicated API logger
error_logger = get_logger("app.errors")
security_logger = SecurityLogger()


# API Debug Logging Utility
class APIDebugLogger:
    """Specialized logger for API request/response debugging"""
    
    def __init__(self):
        self.logger = get_logger("app.api")
    
    def debug(self, message: str):
        self.logger.debug(message)
        
    def log_api_start(self, method: str, endpoint: str, client_ip: str, user_id: str = None, request_id: str = None):
        """Log API call start"""
        user_info = f"User:{user_id}" if user_id else "Anonymous"
        req_id = f"ReqID:{request_id}" if request_id else ""
        self.logger.debug(f"🚀 API START - {method} {endpoint} - IP:{client_ip} - {user_info} {req_id}")
    
    def log_api_params(self, params: dict = None, query_params: dict = None, body_size: int = 0):
        """Log API parameters and body info"""
        if params:
            self.logger.debug(f"📥 API PARAMS - Path: {params}")
        if query_params:
            self.logger.debug(f"🔍 API QUERY - Query: {query_params}")
        if body_size > 0:
            self.logger.debug(f"📦 API BODY - Size: {body_size} bytes")
    
    def log_database_operation(self, operation: str, table: str = None, query_time: float = None, row_count: int = None):
        """Log database operations"""
        db_info = f"Table:{table}" if table else "Multiple"
        time_info = f"Time:{query_time:.3f}s" if query_time else ""
        count_info = f"Rows:{row_count}" if row_count is not None else ""
        self.logger.debug(f"🗄️  DB {operation.upper()} - {db_info} {time_info} {count_info}")
    
    def log_external_call(self, service: str, endpoint: str, response_time: float = None, status_code: int = None):
        """Log external service calls"""
        time_info = f"Time:{response_time:.3f}s" if response_time else ""
        status_info = f"Status:{status_code}" if status_code else ""
        self.logger.debug(f"🌐 EXTERNAL CALL - {service}:{endpoint} {time_info} {status_info}")
    
    def log_processing_step(self, step: str, details: str = None, processing_time: float = None):
        """Log processing steps"""
        time_info = f"Time:{processing_time:.3f}s" if processing_time else ""
        detail_info = f"Details:{details}" if details else ""
        self.logger.debug(f"⚙️  PROCESSING - {step} {detail_info} {time_info}")
    
    def log_api_end(self, method: str, endpoint: str, status_code: int, response_time: float, response_size: int = 0, error: str = None):
        """Log API call completion"""
        status_emoji = "✅" if 200 <= status_code < 300 else "⚠️" if 300 <= status_code < 400 else "❌"
        size_info = f"Size:{response_size}B" if response_size > 0 else ""
        error_info = f"Error:{error}" if error else ""
        self.logger.debug(f"{status_emoji} API END - {method} {endpoint} - Status:{status_code} Time:{response_time:.3f}s {size_info} {error_info}")
    
    def log_validation_error(self, field: str, error: str, value: str = None):
        """Log validation errors"""
        value_info = f"Value:'{value}'" if value else ""
        self.logger.debug(f"🚫 VALIDATION ERROR - Field:{field} Error:{error} {value_info}")
    
    def log_business_logic(self, operation: str, result: str, details: dict = None):
        """Log business logic operations"""
        detail_info = f"Details:{details}" if details else ""
        self.logger.debug(f"🏢 BUSINESS LOGIC - {operation} Result:{result} {detail_info}")


# Global API debug logger instance
api_debug_logger = APIDebugLogger()