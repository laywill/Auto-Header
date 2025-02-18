from ..core import FileHandler, FileSection
from typing import Dict, List, Set, Tuple


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
        processed_indices: Set[int] = set()

        def extract_help_block(start_idx: int) -> Tuple[List[str], int]:
            """Extract a help comment block."""
            block_lines = [lines[start_idx]]
            end_idx = start_idx
            brace_level = 1

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

            # Count initial parentheses in first line
            first_line = lines[start_idx]
            paren_count += first_line.count("(") - 1  # -1 because we started with 1
            paren_count -= first_line.count(")")
            brace_count += first_line.count("{") - first_line.count("}")

            while end_idx + 1 < len(lines):
                end_idx += 1
                line = lines[end_idx]

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

            # Handle help blocks (must come before param blocks)
            elif stripped.startswith("<#"):
                block_lines, end_idx = extract_help_block(i)
                block_text = "\n".join(block_lines)

                if ".SYNOPSIS" in block_text or ".DESCRIPTION" in block_text:
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

            # Handle param blocks
            elif stripped.lower().startswith("param"):
                block_lines, end_idx = extract_param_block(i)
                sections.append(FileSection("\n".join(block_lines), is_special=True))
                processed_indices.update(range(i, end_idx + 1))
                i = end_idx

            # Handle CmdletBinding attribute
            elif stripped.startswith("[CmdletBinding"):
                sections.append(FileSection(line, is_special=True))
                processed_indices.add(i)

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
        cmdlet_binding_sections = []
        param_sections = []
        main_sections = []

        for section in sections:
            if section.is_copyright:
                continue
            elif section.is_special:
                content = section.content.strip()
                if content.startswith("#requires"):
                    requires_sections.append(section.content)
                elif content.startswith("using"):
                    using_sections.append(section.content)
                elif content.startswith("<#") and (
                    ".SYNOPSIS" in content or ".DESCRIPTION" in content
                ):
                    help_sections.append(section.content)
                elif content.startswith("[CmdletBinding"):
                    cmdlet_binding_sections.append(section.content)
                elif content.lower().startswith("param"):
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

        # 3. Help comment block
        if help_sections:
            output_parts.extend(help_sections)
            output_parts.append("")

        # 4. CmdletBinding (if present)
        if cmdlet_binding_sections:
            output_parts.extend(cmdlet_binding_sections)
            output_parts.append("")

        # 5. Param block
        if param_sections:
            output_parts.extend(param_sections)
            output_parts.append("")

        # 6. Copyright header
        output_parts.append(new_header.rstrip())
        output_parts.append("")

        # 7. Main content
        if main_sections:
            output_parts.extend(main_sections)

        return "\n".join(output_parts) + "\n"
