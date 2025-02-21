from ..core import FileHandler, FileSection
from typing import Dict, List, Set


class PythonHandler(FileHandler):
    """Handler for Python files with support for shebangs, encoding, and docstrings."""

    @property
    def file_extensions(self) -> List[str]:
        return [".py"]

    @property
    def comment_syntax(self) -> Dict[str, str]:
        return {"start": "#", "end": ""}

    @property
    def special_patterns(self) -> List[str]:
        return [
            r"^#!.*",  # shebang
            r"^# -\*-.*-\*-$",  # encoding
            r"^from __future__.*",  # future imports
        ]

    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse Python file content preserving special sections and structure."""
        lines = content.splitlines()
        sections: List[FileSection] = []
        processed_indices: Set[int] = set()

        i = 0
        while i < len(lines):
            if i in processed_indices:
                i += 1
                continue

            line = lines[i].rstrip()
            stripped = line.strip()

            # Handle shebang and special lines
            if self.is_special_line(line):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

            # Handle copyright comments
            elif stripped.startswith("#"):
                comment_lines = [line]
                while i + 1 < len(lines) and lines[i + 1].strip().startswith("#"):
                    i += 1
                    comment_lines.append(lines[i])
                comment_text = "\n".join(comment_lines)
                sections.append(
                    FileSection(
                        comment_text,
                        is_comment_block=True,
                        is_copyright=self.is_copyright_text(comment_text),
                    )
                )
                processed_indices.add(i)

            # Handle remaining content as a single section to preserve structure
            elif not i in processed_indices:
                remaining_lines = []
                while i < len(lines):
                    if i not in processed_indices:
                        remaining_lines.append(lines[i])
                    i += 1
                if remaining_lines:
                    sections.append(FileSection("\n".join(remaining_lines)))
                break

            i += 1

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output with correct Python file structure."""
        output_parts: List[str] = []

        # Add shebang and special sections first
        special_sections = [s for s in sections if s.is_special]
        if special_sections:
            output_parts.extend(s.content for s in special_sections)
            output_parts.append("")

        # Add the copyright header
        output_parts.append(new_header.rstrip())

        # Add remaining content preserving structure
        content_sections = [
            s for s in sections if not s.is_special and not s.is_copyright
        ]

        if content_sections:
            output_parts.append("")
            output_parts.extend(s.content for s in content_sections)

        return "\n".join(output_parts) + "\n"
