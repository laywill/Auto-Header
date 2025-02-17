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

    def should_ignore(self, filepath: str) -> bool:
        """
        Check if a file should be ignored based on ignore patterns.

        Args:
            filepath: Path to the file to check

        Returns:
            bool: True if file should be ignored, False otherwise
        """
        return any(
            fnmatch.fnmatch(filepath, pattern) for pattern in self.ignore_patterns
        )

    def get_comment_syntax(self, filepath: str) -> Optional[Dict[str, str]]:
        """
        Get the appropriate comment syntax for a given file.

        Args:
            filepath: Path to the file

        Returns:
            Optional[Dict[str, str]]: Dictionary with 'start' and 'end' comment markers
        """
        _, ext = os.path.splitext(filepath)
        return self.COMMENT_SYNTAX.get(ext.lower())

    def format_header(self, comment_syntax: Dict[str, str]) -> str:
        """
        Format the header text with appropriate comment markers.

        Args:
            comment_syntax: Dictionary containing start and end comment markers

        Returns:
            str: Formatted header with comment markers
        """
        start, end = comment_syntax["start"], comment_syntax["end"]
        if end:
            return f"{start}\n{self.header_text}\n{end}\n\n"
        return f"{start} {self.header_text}\n\n"

    def has_header(self, content: str, comment_syntax: Dict[str, str]) -> bool:
        """
        Check if file content already contains the header.

        Args:
            content: File content to check
            comment_syntax: Dictionary containing comment syntax

        Returns:
            bool: True if header exists, False otherwise
        """
        header = self.format_header(comment_syntax).strip()
        return content.strip().startswith(header.strip())

    def extract_special_header(self, content: str, filepath: str) -> tuple[str, str]:
        """
        Extract special headers like shebang, encoding declarations, etc.

        Args:
            content: File content to process
            filepath: Path to the file (used to determine file type)

        Returns:
            tuple[str, str]: Special header (if any) and remaining content
        """
        lines = content.splitlines()
        if not lines:
            return "", ""

        special_header = []
        content_start = 0

        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        # Python specific handling
        if ext == ".py":
            # Handle shebang
            if lines[0].startswith("#!"):
                special_header.append(lines[0])
                content_start = 1

            # Handle encoding declaration
            if content_start < len(lines) and (
                lines[content_start].startswith("# -*-")
                or lines[content_start].startswith("# coding=")
                or lines[content_start].startswith("# encoding=")
            ):
                special_header.append(lines[content_start])
                content_start += 1

            # Handle future imports
            while content_start < len(lines) and (
                lines[content_start].strip().startswith("from __future__ import")
                or lines[content_start].strip().startswith("import __future__")
            ):
                special_header.append(lines[content_start])
                content_start += 1

        # YAML specific handling
        elif ext in [".yml", ".yaml"]:
            in_document = False
            for i, line in enumerate(lines[content_start:], start=content_start):
                line_strip = line.strip()
                if line_strip == "---":
                    special_header.append(line)
                    content_start = i + 1
                    in_document = True
                elif in_document and line_strip == "...":
                    # Preserve document end marker in content
                    break
                elif in_document:
                    break

        # Bash specific handling
        elif ext == ".sh":
            # Handle shebang
            if lines[0].startswith("#!"):
                special_header.append(lines[0])
                content_start = 1

            # Handle common shell options and env settings
            while content_start < len(lines):
                line = lines[content_start].strip()
                if (
                    line.startswith("set -")
                    or line.startswith("export ")
                    or line.startswith("declare -")
                    or line == "set -o errexit"
                    or line == "set -o nounset"
                    or line == "set -o pipefail"
                ):
                    special_header.append(lines[content_start])
                    content_start += 1
                else:
                    break

        # PowerShell specific handling
        elif ext == ".ps1":
            # Handle param blocks
            for i, line in enumerate(lines[content_start:], start=content_start):
                line_strip = line.strip()
                if line_strip.startswith("param(") or line_strip == "param":
                    # Capture entire param block
                    param_block = []
                    param_block.append(line)
                    content_start = i + 1
                    open_braces = line_strip.count("(") - line_strip.count(")")

                    while open_braces > 0 and content_start < len(lines):
                        param_block.append(lines[content_start])
                        open_braces += lines[content_start].count("(")
                        open_braces -= lines[content_start].count(")")
                        content_start += 1

                    special_header.extend(param_block)
                    break

            # Handle using and requires statements
            while content_start < len(lines):
                line = lines[content_start].strip()
                if (
                    line.startswith("using ")
                    or line.startswith("requires ")
                    or line.startswith("#requires ")
                ):
                    special_header.append(lines[content_start])
                    content_start += 1
                else:
                    break

        # Terraform specific handling
        elif ext == ".tf":
            # We don't extract terraform blocks as special headers
            # Instead, we ensure our comment block comes before any content
            pass

        # Markdown specific handling
        elif ext in [".md", ".markdown"]:
            # Preserve badges/shields if they exist at the top
            while content_start < len(lines):
                line = lines[content_start].strip()
                if (
                    line.startswith("[![")
                    and line.endswith("]")
                    or line.startswith("![")
                    and line.endswith("]")
                    or line.startswith("<img")
                    and line.endswith(">")
                ):
                    special_header.append(lines[content_start])
                    content_start += 1
                else:
                    break

        remaining_content = "\n".join(lines[content_start:])
        return (
            "\n".join(special_header) + "\n" if special_header else "",
            remaining_content,
        )

    def process_file(self, filepath: str) -> bool:
        """
        Process a single file - add or update header if needed.

        Args:
            filepath: Path to the file to process

        Returns:
            bool: True if file was modified, False otherwise
        """
        if self.should_ignore(filepath):
            return False

        comment_syntax = self.get_comment_syntax(filepath)
        if not comment_syntax:
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if self.has_header(content, comment_syntax):
                return False

            special_header, remaining_content = self.extract_special_header(
                content, filepath
            )
            header = self.format_header(comment_syntax)

            with open(filepath, "w", encoding="utf-8") as f:
                if special_header:
                    f.write(special_header)
                f.write(header + remaining_content.lstrip())
            return True

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return False

    def process_directory(self, directory: str) -> Dict[str, int]:
        """
        Recursively process all files in a directory.

        Args:
            directory: Root directory to start processing from

        Returns:
            Dict[str, int]: Statistics about processed files
        """
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
    parser.add_argument("directory", help="Root directory to process")
    parser.add_argument(
        "--header",
        default="Copyright Example Ltd, UK 2025",
        help="Header text to insert",
    )
    parser.add_argument(
        "--ignore", nargs="*", default=[], help="Glob patterns for files to ignore"
    )

    args = parser.parse_args()

    manager = HeaderManager(args.header, args.ignore)
    stats = manager.process_directory(args.directory)

    print(f"\nProcessing complete:")
    print(f"Files processed: {stats['processed']}")
    print(f"Files modified: {stats['modified']}")
    print(f"Files skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
