#!/usr/bin/env python3
"""
Consolidated error handling utilities for ClAP
Provides consistent error handling patterns across all scripts
"""

import logging
import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps

class ClapError(Exception):
    """Base exception class for ClAP errors"""
    pass

class ConfigurationError(ClapError):
    """Raised when configuration is missing or invalid"""
    pass

class APIError(ClapError):
    """Raised when external API calls fail"""
    pass

class FileOperationError(ClapError):
    """Raised when file operations fail"""
    pass

def setup_logging(name: str, log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Set up consistent logging configuration
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file path
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger(name)

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[str]]:
    """
    Safely execute a function and return success status, result, and error message
    
    Returns:
        (success, result, error_message)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        return False, None, error_msg

def handle_api_error(response, operation: str = "API call"):
    """
    Standard error handling for API responses
    
    Args:
        response: Response object from requests
        operation: Description of the operation for error messages
    
    Returns:
        (success, error_message)
    """
    if response.status_code in [200, 201, 204]:
        return True, None
    
    error_msg = f"{operation} failed with status {response.status_code}"
    
    try:
        error_data = response.json()
        if 'message' in error_data:
            error_msg += f": {error_data['message']}"
        elif 'error' in error_data:
            error_msg += f": {error_data['error']}"
    except:
        if response.text:
            error_msg += f": {response.text}"
    
    return False, error_msg

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry a function on failure with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Multiplier for delay after each attempt
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            raise last_exception
        return wrapper
    return decorator

def exit_with_error(message: str, code: int = 1):
    """
    Print error message and exit with specified code
    
    Args:
        message: Error message to display
        code: Exit code (default: 1)
    """
    print(f"❌ Error: {message}", file=sys.stderr)
    sys.exit(code)

def format_exception(e: Exception, include_traceback: bool = False) -> str:
    """
    Format an exception for display
    
    Args:
        e: The exception to format
        include_traceback: Whether to include full traceback
    
    Returns:
        Formatted error string
    """
    error_msg = f"{type(e).__name__}: {str(e)}"
    
    if include_traceback:
        error_msg += "\n\nTraceback:\n" + traceback.format_exc()
    
    return error_msg

class ErrorCollector:
    """
    Collect errors during batch operations
    """
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def add_error(self, context: str, error: Exception):
        """Add an error with context"""
        self.errors.append({
            'context': context,
            'error': format_exception(error),
            'type': type(error).__name__
        })
    
    def add_warning(self, context: str, message: str):
        """Add a warning with context"""
        self.warnings.append({
            'context': context,
            'message': message
        })
    
    def has_errors(self) -> bool:
        """Check if any errors were collected"""
        return len(self.errors) > 0
    
    def get_summary(self) -> str:
        """Get a summary of all errors and warnings"""
        summary = []
        
        if self.errors:
            summary.append(f"❌ {len(self.errors)} error(s):")
            for error in self.errors:
                summary.append(f"  - {error['context']}: {error['error']}")
        
        if self.warnings:
            summary.append(f"⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                summary.append(f"  - {warning['context']}: {warning['message']}")
        
        return "\n".join(summary) if summary else "✅ No errors or warnings"