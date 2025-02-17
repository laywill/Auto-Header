"""Auto Header tool for maintaining copyright and license headers in repository files."""

import os
import fnmatch
import argparse
from typing import Dict, List, Optional


class AutoHeader:
    # Dictionary mapping file extensions to their comment syntax
    COMMENT_SYNTAX = {
        ".py": {"start": "#", "end": ""},
        ".yaml": {"start": "#", "end": ""},
        ".yml": {"start": "#", "end": ""},
        ".sh": {"start": "#", "end": ""},
        ".ps1": {"start": "<#", "end": "#>"},
        ".tf": {"start": "/*", "end": "*/"},
        ".tfvars": {"start": "#", "end": ""},
        ".md": {"start": "<!--", "end": "-->"},
        ".markdown": {"start": "<!--", "end": "-->"},
    }

    def __init__(self, header_text: str, ignore_patterns: Optional[List[str]] = None):
        """
        Initialize the AutoHeader with header text and ignore patterns.

        Args:
            header_text: The copyright or header text to insert
            ignore_patterns: List of glob patterns for files to ignore
        """
        self.header_text = header_text
        self.ignore_patterns = ignore_patterns or []
