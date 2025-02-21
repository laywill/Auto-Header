from ..core import FileHandler, FileSection
from typing import Dict, List, Set


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
