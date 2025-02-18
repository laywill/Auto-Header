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
        """
        Create the final output with correct PowerShell section ordering.

        Header placement rules:
        1. After param block if it exists
        2. After using statement if only using and requires exist
        3. After requires statement if only requires exists
        4. After using statement if only using exists
        5. At the start if no special sections exist
        """
        # Group sections by type using list comprehensions for efficiency
        requires = [
            s.content
            for s in sections
            if s.is_special and s.content.strip().startswith("#requires")
        ]
        using = [
            s.content
            for s in sections
            if s.is_special and s.content.strip().startswith("using")
        ]
        param = [
            s.content
            for s in sections
            if s.is_special
            and s.content.strip().lower().startswith(("param", "[cmdletbinding"))
        ]
        content = [
            s.content
            for s in sections
            if not s.is_special and not s.is_copyright and not s.is_comment_block
        ]

        # Build output sections in order
        output_parts: List[str] = []

        # Add requires if present
        if requires:
            output_parts.extend(requires)

        # Add using statements if present
        if using:
            if output_parts:
                output_parts.append("")
            output_parts.extend(using)

        # Add param blocks if present
        if param:
            if output_parts:
                output_parts.append("")
            output_parts.extend(param)

        # Add copyright header at the correct position
        if output_parts:
            output_parts.append("")
        output_parts.append(new_header.rstrip())

        # Add remaining content after header
        if content:
            output_parts.append("")
            output_parts.extend(filter(None, content))  # Filter out empty strings

        return "\n".join(output_parts) + "\n"
