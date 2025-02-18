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
            r'^""".*?"""$',  # single-line docstring
            r'^""".*$',  # start of multi-line docstring
        ]

    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse Python file content preserving special sections."""
        lines = content.splitlines()
        sections: List[FileSection] = []
        current_lines: List[str] = []
        in_docstring = False
        processed_indices: Set[int] = set()

        i = 0
        while i < len(lines):
            if i in processed_indices:
                i += 1
                continue

            line = lines[i].rstrip()
            stripped = line.strip()

            # Handle docstrings
            if stripped.startswith('"""'):
                if stripped.endswith('"""') and len(stripped) > 3:
                    # Single-line docstring
                    sections.append(FileSection(line, is_special=True))
                    processed_indices.add(i)
                else:
                    # Multi-line docstring
                    docstring_lines = [line]
                    in_docstring = True
                    i += 1
                    while i < len(lines) and in_docstring:
                        line = lines[i]
                        docstring_lines.append(line)
                        if '"""' in line:
                            in_docstring = False
                        i += 1
                        processed_indices.add(i - 1)
                    sections.append(
                        FileSection("\n".join(docstring_lines), is_special=True)
                    )
                    continue

            # Handle special lines (shebang, encoding, future imports)
            elif self.is_special_line(line):
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

            # Handle remaining content
            elif stripped and i not in processed_indices:
                sections.append(FileSection(line))
                processed_indices.add(i)

            i += 1

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output with correct Python file structure."""
        output_parts: List[str] = []

        # Collect sections by type
        special_top = []  # shebang, encoding, future imports
        docstrings = []
        content = []

        for section in sections:
            if section.is_copyright:
                continue

            if section.is_special:
                text = section.content.strip()
                if text.startswith('"""'):
                    docstrings.append(section.content)
                else:
                    special_top.append(section.content)
            elif not section.is_comment_block:
                content.append(section.content)

        # Add sections in correct order
        if special_top:
            output_parts.extend(special_top)
            output_parts.append("")

        output_parts.append(new_header.rstrip())

        if docstrings:
            output_parts.append("")
            output_parts.extend(docstrings)

        if content:
            output_parts.append("")
            output_parts.extend(filter(None, content))

        return "\n".join(output_parts) + "\n"
