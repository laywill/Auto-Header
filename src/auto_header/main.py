"""Auto Header tool for maintaining copyright and license headers in repository files."""

import os
import re
import fnmatch
import argparse
from typing import Dict, List, Optional, Tuple


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
        """Check if a file should be ignored based on ignore patterns."""
        return any(
            fnmatch.fnmatch(filepath, pattern) for pattern in self.ignore_patterns
        )

    def get_comment_syntax(self, filepath: str) -> Optional[Dict[str, str]]:
        """Get the appropriate comment syntax for a given file."""
        _, ext = os.path.splitext(filepath)
        return self.COMMENT_SYNTAX.get(ext.lower())

    def format_header(self, comment_syntax: Dict[str, str]) -> str:
        """Format the header text with appropriate comment markers."""
        start, end = comment_syntax["start"], comment_syntax["end"]

        # Split header into lines, preserving intentional line breaks
        header_lines = self.header_text.splitlines()

        if end:  # Multi-line comment style (like /* */)
            if len(header_lines) == 1:
                return f"{start} {header_lines[0]} {end}\n\n"
            else:
                # Format each line within the comment markers
                formatted_lines = [f"{start}"]
                formatted_lines.extend(f" * {line}" for line in header_lines)
                formatted_lines.append(f" {end}")
                return "\n".join(formatted_lines) + "\n\n"
        else:  # Single-line comment style (like #)
            formatted_lines = [f"{start} {line}" for line in header_lines]
            return "\n".join(formatted_lines) + "\n\n"

    def is_copyright_header(self, text: str) -> bool:
        """
        Check if a text block is a copyright header.

        Criteria:
        1. Contains 'copyright' (case insensitive)
        2. Contains 'license' or 'licence' (case insensitive)
        3. Matches our header except for date differences
        """
        # Normalize text for comparison (strip comments and whitespace)
        normalized = re.sub(r"[#/*<!>-]+", "", text).strip()
        target_normalized = re.sub(r"[#/*<!>-]+", "", self.header_text).strip()

        # If it's nearly identical (ignoring dates), it's a header
        if re.sub(r"\d{4}", "0000", normalized) == re.sub(
            r"\d{4}", "0000", target_normalized
        ):
            return True

        normalized_lower = normalized.lower()
        return any(
            word in normalized_lower for word in ["copyright", "license", "licence"]
        )

    def extract_special_header(
        self, content: str, filepath: str
    ) -> Tuple[str, str, str]:
        """
        Extract special headers and existing copyright header if present.

        Returns:
            Tuple[str, str, str]: (special_header, existing_copyright, remaining_content)
        """
        lines = content.splitlines()
        if not lines:
            return "", "", ""

        special_header_lines = []
        copyright_header_lines = []
        content_lines = []

        # Track our parsing state
        in_comment_block = False
        found_copyright = False
        comment_block_lines = []

        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        # Process lines
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Handle special headers first (shebang, etc.)
            if i == 0 and stripped.startswith("#!"):
                special_header_lines.append(line)
                i += 1
                continue

            # Handle document markers for YAML
            if ext in [".yml", ".yaml"] and stripped == "---":
                special_header_lines.append(line)
                i += 1
                continue

            # Skip empty lines between special headers
            if not stripped and not content_lines and not copyright_header_lines:
                special_header_lines.append(line)
                i += 1
                continue

            # Check for comment blocks
            if not found_copyright:
                comment_start = False
                if stripped.startswith("/*"):
                    in_comment_block = True
                    comment_start = True
                elif stripped.endswith("*/"):
                    in_comment_block = False
                elif stripped.startswith("<!--"):
                    in_comment_block = True
                    comment_start = True
                elif stripped.endswith("-->"):
                    in_comment_block = False
                elif stripped.startswith("#") or stripped.startswith("<#"):
                    comment_block_lines.append(line)
                    i += 1
                    continue

                if comment_start:
                    comment_block_lines = [line]
                    i += 1
                    continue

                if in_comment_block:
                    comment_block_lines.append(line)
                    i += 1
                    continue

                # End of comment block or standalone comment
                if comment_block_lines:
                    comment_text = "\n".join(comment_block_lines)
                    if self.is_copyright_header(comment_text):
                        copyright_header_lines.extend(comment_block_lines)
                        found_copyright = True
                    else:
                        content_lines.extend(comment_block_lines)
                    comment_block_lines = []

            if not comment_block_lines:
                content_lines.append(line)
            i += 1

        # Handle any remaining comment block
        if comment_block_lines:
            comment_text = "\n".join(comment_block_lines)
            if self.is_copyright_header(comment_text):
                copyright_header_lines.extend(comment_block_lines)
            else:
                content_lines.extend(comment_block_lines)

        return (
            "\n".join(special_header_lines) + "\n" if special_header_lines else "",
            "\n".join(copyright_header_lines) + "\n" if copyright_header_lines else "",
            "\n".join(content_lines),
        )

    def process_file(self, filepath: str) -> bool:
        """Process a single file - add or update header if needed."""
        if self.should_ignore(filepath):
            return False

        comment_syntax = self.get_comment_syntax(filepath)
        if not comment_syntax:
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            special_header, existing_copyright, remaining_content = (
                self.extract_special_header(content, filepath)
            )
            new_header = self.format_header(comment_syntax)

            # If existing copyright matches exactly (including whitespace), no update needed
            if existing_copyright and existing_copyright.strip() == new_header.strip():
                return False

            # Combine all parts
            updated_content = ""
            if special_header:
                updated_content += special_header
            updated_content += new_header
            if remaining_content:
                updated_content += remaining_content

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return True

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return False

    def process_directory(self, directory: str) -> Dict[str, int]:
        """Recursively process all files in a directory."""
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
    parser.add_argument("--directory", help="Root directory to process")
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
