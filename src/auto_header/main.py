"""Auto Header tool for maintaining copyright and license headers in repository files."""

import os
import re
import fnmatch
import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class FileSection:
    """Represents a section of a file with its content and metadata."""

    content: str
    is_special: bool = False
    is_copyright: bool = False
    is_comment_block: bool = False
    comment_syntax: Optional[Dict[str, str]] = None


class AutoHeader:
    # Dictionary mapping file extensions to their comment syntax and special rules
    FILE_TYPES = {
        ".py": {
            "comment": {"start": "#", "end": ""},
            "special_patterns": [r"^#!.*", r"^# -*-.*"],
        },
        ".yaml": {
            "comment": {"start": "#", "end": ""},
            "special_patterns": [r"^---$"],
            "preserve_markers": True,
        },
        ".yml": {
            "comment": {"start": "#", "end": ""},
            "special_patterns": [r"^---$"],
            "preserve_markers": True,
        },
        ".sh": {"comment": {"start": "#", "end": ""}, "special_patterns": [r"^#!.*"]},
        ".ps1": {
            "comment": {"start": "<#", "end": "#>"},
            "special_patterns": [
                r"^#requires.*",
                r"^param\s*\(.*?\)(\s*{)?$",
                r"^\[CmdletBinding.*?\]$",
            ],
            "multiline_blocks": ["param"],
        },
        ".tf": {"comment": {"start": "/*", "end": "*/"}},
        ".tfvars": {"comment": {"start": "#", "end": ""}},
        ".md": {"comment": {"start": "<!--", "end": "-->"}},
        ".markdown": {"comment": {"start": "<!--", "end": "-->"}},
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
        # Compile special patterns for performance
        self.compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for ext, config in self.FILE_TYPES.items():
            if "special_patterns" in config:
                self.compiled_patterns[ext] = [
                    re.compile(pattern) for pattern in config["special_patterns"]
                ]

    def should_ignore(self, filepath: str) -> bool:
        """Check if a file should be ignored based on ignore patterns."""
        return any(
            fnmatch.fnmatch(filepath, pattern) for pattern in self.ignore_patterns
        )

    def get_file_config(self, filepath: str) -> Optional[Dict]:
        """Get the configuration for a given file type."""
        _, ext = os.path.splitext(filepath)
        return self.FILE_TYPES.get(ext.lower())

    def format_header(self, comment_syntax: Dict[str, str]) -> str:
        """Format the header text with appropriate comment markers."""
        start, end = comment_syntax["start"], comment_syntax["end"]
        header_lines = self.header_text.splitlines()

        if end:  # Multi-line comment style
            if len(header_lines) == 1:
                return f"{start} {header_lines[0]} {end}\n"
            else:
                formatted_lines = [f"{start}"]
                formatted_lines.extend(f" * {line}" for line in header_lines)
                formatted_lines.append(f" {end}")
                return "\n".join(formatted_lines) + "\n"
        else:  # Single-line comment style
            return "\n".join(f"{start} {line}" for line in header_lines) + "\n"

    def is_special_line(self, line: str, ext: str) -> bool:
        """Check if a line matches any special patterns for the file type."""
        if ext not in self.compiled_patterns:
            return False
        return any(
            pattern.match(line.strip()) for pattern in self.compiled_patterns[ext]
        )

    def is_copyright_text(self, text: str) -> bool:
        """
        Check if text contains copyright or license information.
        Handles both exact matches and general copyright indicators.
        """
        normalized = re.sub(r"\s+", " ", text.lower())
        # Check for exact match (ignoring dates and whitespace)
        target = re.sub(r"\s+", " ", self.header_text.lower())
        if re.sub(r"\d{4}", "0000", normalized) == re.sub(r"\d{4}", "0000", target):
            return True

        # Check for copyright/license keywords
        return any(word in normalized for word in ["copyright", "license", "licence"])

    def parse_file_content(self, content: str, filepath: str) -> List[FileSection]:
        """
        Parse file content into sections while preserving special elements.
        Returns list of FileSection objects in correct order.
        """
        lines = content.splitlines()
        sections: List[FileSection] = []
        current_section = []
        in_special_block = False
        in_comment_block = False

        file_config = self.get_file_config(filepath)
        if not file_config:
            return [FileSection(content)]

        comment_syntax = file_config["comment"]
        ext = os.path.splitext(filepath)[1].lower()

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Handle multiline blocks (like PowerShell param blocks)
            if file_config.get("multiline_blocks") and any(
                line.strip().lower().startswith(block)
                for block in file_config["multiline_blocks"]
            ):
                current_section.append(line)
                i += 1
                # Collect until matching closing brace
                brace_count = line.count("{") - line.count("}")
                while i < len(lines) and (brace_count > 0 or "}" not in lines[i]):
                    current_section.append(lines[i])
                    brace_count += lines[i].count("{") - lines[i].count("}")
                    i += 1
                if i < len(lines):  # Add closing line
                    current_section.append(lines[i])
                sections.append(
                    FileSection("\n".join(current_section), is_special=True)
                )
                current_section = []
                i += 1
                continue

            # Check for special lines (shebang, markers, etc.)
            if self.is_special_line(line, ext):
                if current_section:
                    sections.append(FileSection("\n".join(current_section)))
                    current_section = []
                sections.append(FileSection(line, is_special=True))
                i += 1
                continue

            # Handle comment blocks
            if comment_syntax["end"]:  # Multiline comments
                if line.strip().startswith(comment_syntax["start"]):
                    if current_section:
                        sections.append(FileSection("\n".join(current_section)))
                        current_section = []
                    comment_lines = [line]
                    i += 1
                    while i < len(lines) and comment_syntax["end"] not in lines[i]:
                        comment_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        comment_lines.append(lines[i])
                        i += 1
                    comment_text = "\n".join(comment_lines)
                    sections.append(
                        FileSection(
                            comment_text,
                            is_comment_block=True,
                            is_copyright=self.is_copyright_text(comment_text),
                            comment_syntax=comment_syntax,
                        )
                    )
                    continue
            else:  # Single-line comments
                if line.strip().startswith(comment_syntax["start"]):
                    if current_section:
                        sections.append(FileSection("\n".join(current_section)))
                        current_section = []
                    comment_lines = [line]
                    while i + 1 < len(lines) and lines[i + 1].strip().startswith(
                        comment_syntax["start"]
                    ):
                        i += 1
                        comment_lines.append(lines[i])
                    comment_text = "\n".join(comment_lines)
                    sections.append(
                        FileSection(
                            comment_text,
                            is_comment_block=True,
                            is_copyright=self.is_copyright_text(comment_text),
                            comment_syntax=comment_syntax,
                        )
                    )
                    i += 1
                    continue

            current_section.append(line)
            i += 1

        if current_section:
            sections.append(FileSection("\n".join(current_section)))

        return sections

    def process_file(self, filepath: str) -> bool:
        """Process a single file - add or update header if needed."""
        if self.should_ignore(filepath):
            return False

        file_config = self.get_file_config(filepath)
        if not file_config:
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            sections = self.parse_file_content(content, filepath)
            new_header = self.format_header(file_config["comment"])

            # Check if copyright header already exists and matches
            existing_copyright = next((s for s in sections if s.is_copyright), None)
            if (
                existing_copyright
                and existing_copyright.content.strip() == new_header.strip()
            ):
                return False

            # Build new content with correct ordering
            new_sections = []
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()

            # Special handling for PowerShell files
            if ext == ".ps1":
                # First: #requires statements
                requires_sections = [
                    s
                    for s in sections
                    if s.is_special and s.content.strip().startswith("#requires")
                ]
                new_sections.extend(requires_sections)

                # Second: using statements
                using_sections = [
                    s
                    for s in sections
                    if not s.is_special and s.content.strip().startswith("using")
                ]
                new_sections.extend(using_sections)

                # Third: param blocks and cmdlet bindings
                param_sections = [
                    s
                    for s in sections
                    if s.is_special
                    and (
                        s.content.strip().startswith("param")
                        or s.content.strip().startswith("[CmdletBinding")
                    )
                ]
                new_sections.extend(param_sections)

                # Fourth: copyright header
                new_sections.append(FileSection(new_header, is_copyright=True))

                # Finally: remaining content
                remaining_sections = [
                    s
                    for s in sections
                    if s not in requires_sections
                    and s not in using_sections
                    and s not in param_sections
                    and not s.is_copyright
                ]
                new_sections.extend(remaining_sections)
            else:
                # For non-PowerShell files, maintain current ordering
                special_sections = [s for s in sections if s.is_special]
                if special_sections:
                    new_sections.extend(special_sections)

                new_sections.append(FileSection(new_header, is_copyright=True))

                remaining_sections = [
                    s for s in sections if not s.is_special and not s.is_copyright
                ]
                if remaining_sections:
                    new_sections.extend(remaining_sections)

            # Join sections with appropriate spacing
            output_parts = []
            for i, section in enumerate(new_sections):
                if i > 0 and (section.is_special or new_sections[i - 1].is_special):
                    output_parts.append(section.content)
                else:
                    output_parts.append(section.content.strip())

            updated_content = "\n\n".join(output_parts) + "\n"

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
