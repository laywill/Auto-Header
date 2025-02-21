"""Auto Header tool for maintaining copyright and license headers in repository files."""

import os
import re
import fnmatch
import argparse

from typing import Dict, List, Optional, Type
from .core import FileHandler
from .handlers import HANDLERS

import logging
from typing import Dict, List, Optional, Type
from .errors import AutoHeaderError, FileOperationError, ConfigurationError, ErrorLevel

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class AutoHeader:
    """Main class for managing file headers across a repository."""

    def __init__(
        self,
        header_text: str,
        ignore_patterns: Optional[List[str]] = None,
        backup_files: bool = True,
    ):
        if not header_text.strip():
            raise ConfigurationError("Header text cannot be empty")

        self.header_text = header_text
        self.ignore_patterns = ignore_patterns or []
        self.backup_files = backup_files
        self.handlers: Dict[str, FileHandler] = {}
        self.errors: List[Dict] = []

        # Register all handlers
        for handler_class in HANDLERS:
            self._register_handler(handler_class)

    def _backup_file(self, filepath: str) -> None:
        """Create backup of original file."""
        import shutil

        backup_path = filepath + ".bak"
        try:
            shutil.copy2(filepath, backup_path)
        except Exception as e:
            raise FileOperationError(
                f"Failed to create backup: {str(e)}",
                file=filepath,
                context={"backup_path": backup_path},
            )

    def _register_handler(self, handler_class: Type[FileHandler]) -> None:
        """Register a file handler for its supported extensions."""
        handler = handler_class(self.header_text)
        for ext in handler.file_extensions:
            self.handlers[ext] = handler

    def should_ignore(self, filepath: str) -> bool:
        """Check if a file should be ignored."""
        return any(
            fnmatch.fnmatch(filepath, pattern) for pattern in self.ignore_patterns
        )

    def get_error_report(self) -> Dict[str, Any]:
        """Generate error report for CI integration."""
        return {
            "total_errors": len(self.errors),
            "by_level": {
                level.value: len([e for e in self.errors if e["level"] == level.value])
                for level in ErrorLevel
            },
            "errors": self.errors,
        }

    def process_file(self, filepath: str) -> bool:
        """Process a single file."""
        if self.should_ignore(filepath):
            logger.debug(f"Ignoring file: {filepath}")
            return False

        _, ext = os.path.splitext(filepath)
        handler = self.handlers.get(ext.lower())
        if not handler:
            logger.debug(f"No handler for extension: {ext}")
            return False

        try:
            if self.backup_files:
                self._backup_file(filepath)

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            handler.current_file = filepath  # Set context for error handling
            sections = handler.parse_file_content(content)
            new_header = handler.format_header()

            # Check if copyright header already exists and matches
            existing_copyright = next((s for s in sections if s.is_copyright), None)
            if (
                existing_copyright
                and existing_copyright.content.strip() == new_header.strip()
            ):
                return False

            # Create output with correct ordering
            updated_content = handler.create_output(sections, new_header)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"Updated header in {filepath}")
            return True

        except AutoHeaderError as e:
            self.errors.append(e.to_dict())
            if e.level == ErrorLevel.FATAL:
                raise
            logger.error(f"{e.level.value}: {e.message} in {filepath}")
            return False
        except Exception as e:
            error = FileOperationError(
                str(e), file=filepath, context={"error_type": type(e).__name__}
            )
            self.errors.append(error.to_dict())
            logger.error(f"Unexpected error in {filepath}: {str(e)}")
            return False
        finally:
            if hasattr(handler, "current_file"):
                delattr(handler, "current_file")

    def process_directory(self, directory: str) -> Dict[str, int]:
        """Process all files in a directory."""
        stats = {"processed": 0, "modified": 0, "skipped": 0}

        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                stats["processed"] += 1

                if self.process_file(filepath):
                    stats["modified"] += 1
                else:
                    stats["skipped"] += 1

        return stats


def main():
    parser = argparse.ArgumentParser(description="Manage file headers in a repository")
    parser.add_argument("--directory", required=True, help="Root directory to process")
    parser.add_argument(
        "--header",
        default="Copyright Example Ltd, UK 2025",
        help="Header text to insert",
    )
    parser.add_argument(
        "--ignore", nargs="*", default=[], help="Glob patterns for files to ignore"
    )

    args = parser.parse_args()

    manager = AutoHeader(args.header, args.ignore)
    stats = manager.process_directory(args.directory)

    print(f"\nProcessing complete:")
    print(f"Files processed: {stats['processed']}")
    print(f"Files modified: {stats['modified']}")
    print(f"Files skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
