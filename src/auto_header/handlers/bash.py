from ..core import FileHandler, FileSection
from typing import Dict, List, Set


class BashHandler(FileHandler):
    """Handler for Bash/Shell script files with support for shebangs and script settings."""

    @property
    def file_extensions(self) -> List[str]:
        return [".sh", ".bash"]

    @property
    def comment_syntax(self) -> Dict[str, str]:
        return {"start": "#", "end": ""}

    @property
    def special_patterns(self) -> List[str]:
        return [
            r"^#!.*$",  # shebang
            r"^#\s*-\*-.*-\*-$",  # editor settings
            r"^set\s+[-+][\w\s]+$",  # shell options (set -e, set -x, etc.)
        ]

    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse Bash file content preserving special sections."""
        lines = content.splitlines()
        sections: List[FileSection] = []
        current_lines: List[str] = []
        processed_indices: Set[int] = set()

        i = 0
        while i < len(lines):
            if i in processed_indices:
                i += 1
                continue

            line = lines[i].rstrip()
            stripped = line.strip()

            # Handle shebang and special settings
            if self.is_special_line(line):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

            # Handle copyright comments
            elif stripped.startswith("#"):
                comment_lines = [line]
                # Collect consecutive comment lines
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

            # Handle shell option settings
            elif stripped.startswith("set "):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

            # Handle remaining content
            elif stripped and i not in processed_indices:
                sections.append(FileSection(line))
                processed_indices.add(i)
            elif not stripped and i not in processed_indices:
                # Preserve empty lines
                sections.append(FileSection(line))
                processed_indices.add(i)

            i += 1

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output with correct Bash script structure."""
        output_parts: List[str] = []

        # Group sections by type
        shebangs = [
            s.content for s in sections if s.is_special and s.content.startswith("#!")
        ]
        settings = [
            s.content
            for s in sections
            if s.is_special
            and (
                s.content.startswith("set ")
                or (s.content.startswith("#") and "-*-" in s.content)
            )
        ]
        content = [
            s.content
            for s in sections
            if not s.is_special and not s.is_copyright and not s.is_comment_block
        ]

        # Add sections in correct order
        if shebangs:
            output_parts.extend(shebangs)
            output_parts.append("")

        output_parts.append(new_header.rstrip())

        if settings:
            output_parts.append("")
            output_parts.extend(settings)

        if content:
            output_parts.append("")
            output_parts.extend(filter(None, content))

        return "\n".join(output_parts) + "\n"
