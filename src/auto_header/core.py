from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import re


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
