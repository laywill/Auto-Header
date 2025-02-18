"""Auto Header tool for maintaining copyright and license headers in repository files."""

import os
import re
import fnmatch
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type


@dataclass
class FileSection:
    """Represents a section of file content with metadata."""

    content: str
    is_special: bool = False
    is_copyright: bool = False
    is_comment_block: bool = False


class FileHandler(ABC):
    """Base class for language-specific file handlers."""

    def __init__(self, header_text: str):
        self.header_text = header_text
        self._compile_patterns()

    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """List of file extensions this handler supports."""
        pass

    @property
    @abstractmethod
    def comment_syntax(self) -> Dict[str, str]:
        """Comment syntax for this language."""
        pass

    @property
    def special_patterns(self) -> List[str]:
        """Regex patterns for special lines (e.g., shebangs)."""
        return []

    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self.compiled_patterns = [
            re.compile(pattern) for pattern in self.special_patterns
        ]

    def format_header(self) -> str:
        """Format the header text with appropriate comment markers."""
        start, end = self.comment_syntax["start"], self.comment_syntax["end"]
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

    def is_special_line(self, line: str) -> bool:
        """Check if a line matches any special patterns."""
        return any(pattern.match(line.strip()) for pattern in self.compiled_patterns)

    def is_copyright_text(self, text: str) -> bool:
        """Check if text contains copyright or license information."""
        normalized = re.sub(r"\s+", " ", text.lower())
        target = re.sub(r"\s+", " ", self.header_text.lower())
        if re.sub(r"\d{4}", "0000", normalized) == re.sub(r"\d{4}", "0000", target):
            return True
        return any(word in normalized for word in ["copyright", "license", "licence"])

    @abstractmethod
    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse file content into sections."""
        pass

    @abstractmethod
    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output from sections and new header."""
        pass


class PowerShellHandler(FileHandler):
    """Handler for PowerShell files."""

    @property
    def file_extensions(self) -> List[str]:
        return [".ps1"]

    @property
    def comment_syntax(self) -> Dict[str, str]:
        return {"start": "<#", "end": "#>"}

    @property
    def special_patterns(self) -> List[str]:
        return [
            r"^#requires.*",
            r"^param\s*\(.*?\)(\s*{)?$",
            r"^\[CmdletBinding.*?\]$",
            r"^using\s+namespace\s+.*",
        ]

    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse PowerShell file content into logical sections."""
        lines = content.splitlines()
        sections: List[FileSection] = []
        current_lines: List[str] = []
        processed_indices: Set[int] = set()

        def extract_block(start_idx: int, block_type: str) -> Tuple[List[str], int]:
            """Extract a block of content starting at the given index."""
            block_lines = [lines[start_idx]]
            end_idx = start_idx

            if block_type == "param":
                brace_count = lines[start_idx].count("{") - lines[start_idx].count("}")
                end_idx += 1
                while end_idx < len(lines) and (
                    brace_count > 0 or "}" not in lines[end_idx]
                ):
                    block_lines.append(lines[end_idx])
                    brace_count += lines[end_idx].count("{") - lines[end_idx].count("}")
                    end_idx += 1
                if end_idx < len(lines):
                    block_lines.append(lines[end_idx])

            elif block_type == "comment":
                end_idx += 1
                while (
                    end_idx < len(lines)
                    and self.comment_syntax["end"] not in lines[end_idx]
                ):
                    block_lines.append(lines[end_idx])
                    end_idx += 1
                if end_idx < len(lines):
                    block_lines.append(lines[end_idx])

            return block_lines, end_idx

        i = 0
        while i < len(lines):
            if i in processed_indices:
                i += 1
                continue

            line = lines[i].rstrip()
            stripped = line.strip()

            # Handle requires statements
            if stripped.startswith("#requires"):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

            # Handle using statements
            elif stripped.startswith("using"):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

            # Handle param blocks
            elif stripped.lower().startswith("param"):
                block_lines, end_idx = extract_block(i, "param")
                sections.append(FileSection("\n".join(block_lines), is_special=True))
                processed_indices.update(range(i, end_idx + 1))
                i = end_idx

            # Handle copyright blocks
            elif stripped.startswith(self.comment_syntax["start"]):
                block_lines, end_idx = extract_block(i, "comment")
                block_text = "\n".join(block_lines)
                sections.append(
                    FileSection(
                        block_text,
                        is_comment_block=True,
                        is_copyright=self.is_copyright_text(block_text),
                    )
                )
                processed_indices.update(range(i, end_idx + 1))
                i = end_idx

            # Handle remaining content
            elif stripped and i not in processed_indices:
                sections.append(FileSection(line))
                processed_indices.add(i)

            i += 1

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create the final output with correct PowerShell section ordering."""
        # Group sections by type
        requires: List[str] = []
        using: List[str] = []
        param: List[str] = []
        content: List[str] = []

        for section in sections:
            if section.is_copyright:
                continue

            stripped = section.content.strip()
            if section.is_special:
                if stripped.startswith("#requires"):
                    requires.append(section.content)
                elif stripped.startswith("using"):
                    using.append(section.content)
                elif stripped.lower().startswith(("param", "[cmdletbinding")):
                    param.append(section.content)
            elif not section.is_comment_block:
                content.append(section.content)

        # Build output with correct ordering and spacing
        output_parts: List[str] = []

        if requires:
            output_parts.extend(requires)

        if using:
            if output_parts:
                output_parts.append("")
            output_parts.extend(using)

        if param:
            if output_parts:
                output_parts.append("")
            output_parts.extend(param)

        if output_parts:
            output_parts.append("")
        output_parts.append(new_header.rstrip())

        if content:
            output_parts.append("")
            output_parts.extend(content)

        return "\n".join(output_parts) + "\n"


class TerraformHandler(FileHandler):
    """Handler for Terraform files."""

    @property
    def file_extensions(self) -> List[str]:
        return [".tf", ".tfvars"]

    @property
    def comment_syntax(self) -> Dict[str, str]:
        return {"start": "/*", "end": "*/"}

    def parse_file_content(self, content: str) -> List[FileSection]:
        lines = content.splitlines()
        sections: List[FileSection] = []
        current_section: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Handle copyright blocks
            if line.strip().startswith(self.comment_syntax["start"]):
                if current_section:
                    sections.append(FileSection("\n".join(current_section)))
                    current_section = []
                comment_lines = [line]
                i += 1
                while i < len(lines) and self.comment_syntax["end"] not in lines[i]:
                    comment_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    comment_lines.append(lines[i])
                comment_text = "\n".join(comment_lines)
                sections.append(
                    FileSection(
                        comment_text,
                        is_comment_block=True,
                        is_copyright=self.is_copyright_text(comment_text),
                    )
                )
                i += 1
                continue

            if line.strip():
                current_section.append(line)
            i += 1

        if current_section:
            sections.append(FileSection("\n".join(current_section)))

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        new_sections = [new_header.rstrip()]

        # Add remaining content
        remaining = [s.content for s in sections if not s.is_copyright]
        if remaining:
            new_sections.append("")
            new_sections.extend(remaining)

        return "\n".join(new_sections) + "\n"


class AutoHeader:
    """Main class for managing file headers across a repository."""

    def __init__(self, header_text: str, ignore_patterns: Optional[List[str]] = None):
        self.header_text = header_text
        self.ignore_patterns = ignore_patterns or []
        self.handlers: Dict[str, FileHandler] = {}

        # Register handlers
        self._register_handler(PowerShellHandler)
        self._register_handler(TerraformHandler)
        # TODO: Add other handlers (Python, Bash, YAML, etc.)

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

    def process_file(self, filepath: str) -> bool:
        """Process a single file."""
        if self.should_ignore(filepath):
            return False

        _, ext = os.path.splitext(filepath)
        handler = self.handlers.get(ext.lower())
        if not handler:
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            sections = handler.parse_file_content(content)

            # Check if copyright header already exists and matches
            existing_copyright = next((s for s in sections if s.is_copyright), None)
            new_header = handler.format_header()

            if (
                existing_copyright
                and existing_copyright.content.strip() == new_header.strip()
            ):
                return False

            # Create output with correct ordering
            updated_content = handler.create_output(sections, new_header)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return True

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return False

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
