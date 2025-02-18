from ..core import FileHandler, FileSection
from typing import Dict, List, Set, Tuple
import re


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

    def create_help_block(self, copyright_text: str) -> str:
        """Create a new help block with copyright information."""
        return f"<#\n.COPYRIGHT\n{copyright_text}\n#>"

    def update_help_block(self, help_block: str, copyright_text: str) -> str:
        """Update an existing help block with copyright information."""
        lines = help_block.splitlines()
        new_lines = []
        copyright_added = False
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(".COPYRIGHT"):
                # Skip the old copyright section
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("."):
                    i += 1
                # Add new copyright
                new_lines.append(".COPYRIGHT")
                new_lines.append(copyright_text)
                copyright_added = True
            else:
                new_lines.append(lines[i])
                i += 1

        # If no copyright section was found, add it before the closing #>
        if not copyright_added:
            if new_lines[-1].strip() == "#>":
                new_lines.insert(-1, ".COPYRIGHT")
                new_lines.insert(-1, copyright_text)
            else:
                new_lines.append(".COPYRIGHT")
                new_lines.append(copyright_text)
                new_lines.append("#>")

        return "\n".join(new_lines)

    def parse_file_content(self, content: str) -> List[FileSection]:
        """Parse PowerShell file content into logical sections."""
        lines = content.splitlines()
        sections: List[FileSection] = []
        processed_indices: Set[int] = set()

        def extract_help_block(start_idx: int) -> Tuple[List[str], int]:
            """Extract a help comment block."""
            block_lines = [lines[start_idx]]
            end_idx = start_idx

            while end_idx + 1 < len(lines):
                end_idx += 1
                line = lines[end_idx]
                block_lines.append(line)
                if "#>" in line:
                    break

            return block_lines, end_idx

        def extract_param_block(start_idx: int) -> Tuple[List[str], int]:
            """Extract a param block, handling nested braces and parentheses."""
            block_lines = [lines[start_idx]]
            end_idx = start_idx
            paren_count = 1  # Start with 1 for the opening parenthesis
            brace_count = 0

            # Skip any leading whitespace/comments before the param block
            while not lines[start_idx].strip().lower().startswith("param"):
                start_idx += 1

            # Count initial parentheses in first line
            first_line = lines[start_idx]
            paren_count += first_line.count("(") - 1  # -1 because we started with 1
            paren_count -= first_line.count(")")
            brace_count += first_line.count("{") - first_line.count("}")

            while end_idx + 1 < len(lines):
                end_idx += 1
                line = lines[end_idx].rstrip()

                # Update counts
                paren_count += line.count("(") - line.count(")")
                brace_count += line.count("{") - line.count("}")

                block_lines.append(line)

                # Check if we've reached the end of the param block
                if paren_count == 0 and brace_count <= 0:
                    break

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

            # Handle help blocks
            elif stripped.startswith("<#"):
                block_lines, end_idx = extract_help_block(i)
                block_text = "\n".join(block_lines)

                # Check if it's a help block
                if any(
                    tag in block_text
                    for tag in [".SYNOPSIS", ".DESCRIPTION", ".COPYRIGHT"]
                ):
                    sections.append(FileSection(block_text, is_special=True))
                else:
                    sections.append(
                        FileSection(
                            block_text,
                            is_comment_block=True,
                            is_copyright=self.is_copyright_text(block_text),
                        )
                    )
                processed_indices.update(range(i, end_idx + 1))
                i = end_idx

            # Handle param blocks - only match top-level param blocks
            elif (
                stripped.lower().startswith("param")
                or (
                    stripped.startswith("[")
                    and i + 1 < len(lines)
                    and lines[i + 1].strip().lower().startswith("param")
                )
            ) and not any(
                # Check previous non-empty lines for function or other block starters
                lines[j].strip()
                and (
                    lines[j].strip().startswith("function")
                    or lines[j].strip().startswith("{")
                )
                for j in range(max(0, i - 5), i)  # Look at previous 5 non-empty lines
            ):
                block_lines, end_idx = extract_param_block(i)
                sections.append(FileSection("\n".join(block_lines), is_special=True))
                processed_indices.update(range(i, end_idx + 1))
                i = end_idx

            # Handle remaining content
            elif not i in processed_indices:
                sections.append(FileSection(line))
                processed_indices.add(i)

            i += 1

        return sections

    def create_output(self, sections: List[FileSection], new_header: str) -> str:
        """Create final output with correct PowerShell section ordering."""
        output_parts: List[str] = []

        # Extract different types of sections
        requires_sections = []
        using_sections = []
        help_sections = []
        param_sections = []
        main_sections = []

        # Process the copyright text to remove any comment markers
        copyright_text = new_header.replace("<#", "").replace("#>", "").strip()

        for section in sections:
            if section.is_copyright:
                continue
            elif section.is_special:
                content = section.content.strip()
                if content.startswith("#requires"):
                    requires_sections.append(section.content)
                elif content.startswith("using"):
                    using_sections.append(section.content)
                elif content.startswith("<#"):
                    help_sections.append(section.content)
                elif content.lower().startswith("param") or (
                    content.startswith("[") and "param" in content.lower()
                ):
                    param_sections.append(section.content)
            elif not section.is_comment_block:
                if section.content.strip():  # Only add non-empty lines
                    main_sections.append(section.content)

        # Build output in PowerShell standard order
        # 1. Requires statements
        if requires_sections:
            output_parts.extend(requires_sections)
            output_parts.append("")

        # 2. Using statements
        if using_sections:
            output_parts.extend(using_sections)
            output_parts.append("")

        # 3. Help block (with copyright)
        if help_sections:
            # Update existing help block with copyright
            updated_help = self.update_help_block(help_sections[0], copyright_text)
            output_parts.append(updated_help)
        else:
            # Create new help block with copyright
            output_parts.append(self.create_help_block(copyright_text))
        output_parts.append("")

        # 4. Param block
        if param_sections:
            output_parts.extend(param_sections)
            output_parts.append("")

        # 5. Main content
        if main_sections:
            output_parts.extend(main_sections)

        return "\n".join(output_parts) + "\n"
