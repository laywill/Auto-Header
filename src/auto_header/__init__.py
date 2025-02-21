"""
Auto-Header - A tool to automatically manage file headers in repositories.

This package provides functionality to insert and maintain copyright headers
and other file-level comments across multiple file types in a repository.
"""

from .main import AutoHeader
from .errors import AutoHeaderError, ErrorLevel

__version__ = "0.1.0"
__all__ = ["AutoHeader", "AutoHeaderError", "ErrorLevel"]
