from ..core import FileHandler, FileSection
from typing import Dict, List, Set
from ..errors import ParseError
from typing import Dict, List, Set


class PythonHandler(FileHandler):
    """Handler for Python files with support for shebangs, encoding, and docstrings."""

    @property
    def file_extensions(self) -> List[str]:
        """List of file extensions this handler supports."""
        return [".py", ".pyi"]  # Added .pyi support

    @property
    def comment_syntax(self) -> Dict[str, str]:
        """Comment syntax options for Python."""
        return {
            "single": {"start": "#", "end": ""},
            "multi": {"start": '"""', "end": '"""'},
        }

    @property
    def special_patterns(self) -> List[str]:
        return [
            r"^#!.*",  # shebang
            r"^#\s*-\*-.*-\*-$",  # encoding
            r"^from\s+__future__\s+import",  # future imports
            r"^#\s*type:\s*ignore",  # type ignore comments
            r"^#\s*pyright:\s*",  # pyright directives
            r"^#\s*mypy:\s*",  # mypy directives
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

    def format_header(self) -> str:
        """Format header with appropriate comment style."""
        try:
            self.validate_header_content(self.header_text)

            # Use multi-line style for multi-line headers
            if "\n" in self.header_text:
                start = self.comment_syntax["multi"]["start"]
                end = self.comment_syntax["multi"]["end"]
                return f"{start}\n{self.header_text}\n{end}\n"

            # Use single-line style for single line headers
            start = self.comment_syntax["single"]["start"]
            return f"{start} {self.header_text}\n"
        except Exception as e:
            raise ParseError(str(e), file=getattr(self, "current_file", None))

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
                i += 1
                continue

            # Handle triple-quoted docstrings/comments
            if stripped.startswith('"""'):
                docstring_lines = [line]
                i += 1
                while i < len(lines) and '"""' not in lines[i]:
                    docstring_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    docstring_lines.append(lines[i])
                    docstring_text = "\n".join(docstring_lines)
                    sections.append(
                        FileSection(
                            docstring_text,
                            is_comment_block=True,
                            is_copyright=self.is_copyright_text(docstring_text),
                        )
                    )
                    processed_indices.add(i)
                i += 1
                continue

            # Handle single-line comments
            if stripped.startswith("#"):
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
                i += 1
                continue

            # Handle remaining content
            if not i in processed_indices:
                sections.append(FileSection(line))
                processed_indices.add(i)
            i += 1

        return sections

    def handle_stub_file(self, content: str) -> str:
        """Special handling for .pyi stub files."""
        lines = content.splitlines()

        # Find insertion point after any imports
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                insert_index = i + 1
            elif line.strip() and not line.startswith(("#", "import", "from")):
                break

        # Insert header after imports
        header = self.format_header()
        lines.insert(insert_index, "")
        lines.insert(insert_index, header.rstrip())

        return "\n".join(lines) + "\n"

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output with correct Python file structure."""
        file_path = getattr(self, "current_file", "")

        # Special handling for .pyi files
        if file_path.endswith(".pyi"):
            content = "\n".join(section.content for section in sections)
            return self.handle_stub_file(content)

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
