from enum import Enum
from typing import Optional, Dict, Any


class ErrorLevel(Enum):
    """Error severity levels."""

    FATAL = "FATAL"  # Abort operation
    ERROR = "ERROR"  # Skip file, continue processing
    WARNING = "WARNING"  # Process with fallback
    INFO = "INFO"  # Informational message


class AutoHeaderError(Exception):
    """Base exception class for Auto-Header errors."""

    def __init__(
        self,
        message: str,
        level: ErrorLevel,
        code: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.level = level
        self.code = code
        self.file = file
        self.line = line
        self.context = context or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "level": self.level.value,
            "code": self.code,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "context": self.context,
        }


class ValidationError(AutoHeaderError):
    """Raised when file content validation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorLevel.ERROR, "E001", **kwargs)


class ParseError(AutoHeaderError):
    """Raised when file parsing fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorLevel.ERROR, "E002", **kwargs)


class FileOperationError(AutoHeaderError):
    """Raised when file operations fail."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorLevel.FATAL, "E003", **kwargs)


class ConfigurationError(AutoHeaderError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorLevel.FATAL, "E004", **kwargs)
