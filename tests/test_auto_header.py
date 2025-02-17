import os
import pytest
import shutil
from textwrap import dedent
from auto_header.main import AutoHeader

class TestAutoHeader:
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a temporary directory for test files."""
        return tmp_path

    @pytest.fixture
    def auto_header(self):
        """Create an AutoHeader instance with test header."""
        return AutoHeader("Copyright Example Ltd, UK 2025")

    def write_file(self, path, content):
        """Helper to write file content with proper line endings."""
        with open(path, 'w', newline='\n') as f:
            f.write(dedent(content).lstrip())

    def read_file(self, path):
        """Helper to read file content with normalized line endings."""
        with open(path, 'r', newline='\n') as f:
            return f.read()

    def test_python_file_with_shebang(self, test_dir, auto_header):
        """Test Python file with shebang and encoding."""
