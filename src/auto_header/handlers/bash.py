import os
import stat
from ..core import FileHandler, FileSection
from ..errors import FileOperationError
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
            r"^set\s+[-+][\w\s]+$",  # shell options
            r"^export\s+\w+=.*$",  # exports
            r"^readonly\s+\w+=.*$",  # readonly variables
            r"^IFS=.*$",  # IFS setting
        ]

    def _preserve_permissions(self, filepath: str) -> None:
        """Preserve original file permissions."""
        try:
            st = os.stat(filepath)
            os.chmod(filepath, st.st_mode)

            # Make file executable if it has a shebang
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#!"):
                    os.chmod(filepath, st.st_mode | stat.S_IEXEC)

        except Exception as e:
            raise FileOperationError(
                f"Failed to preserve permissions: {str(e)}", file=filepath
            )

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
            elif any(
                stripped.startswith(opt)
                for opt in ["set ", "export ", "readonly ", "IFS="]
            ):
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
            and any(
                s.content.startswith(opt)
                for opt in ["set ", "export ", "readonly ", "IFS=", "#"]
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

        result = "\n".join(output_parts) + "\n"

        # Preserve file permissions if file exists
        if hasattr(self, "current_file") and os.path.exists(self.current_file):
            self._preserve_permissions(self.current_file)

        return result
