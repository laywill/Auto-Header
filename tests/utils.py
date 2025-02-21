import os
import shutil
from typing import List, Optional
from pathlib import Path


def get_fixture_path(filename: str) -> str:
    """Get the full path to a test fixture file."""
    base_dir = Path(__file__).parent / "fixtures"
    for root, _, files in os.walk(base_dir):
        if filename in files:
            return str(Path(root) / filename)
    raise FileNotFoundError(f"Fixture {filename} not found")


def create_temp_file(content: str, suffix: str) -> str:
    """Create a temporary file with given content and suffix."""
    import tempfile

    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w") as tmp:
            tmp.write(content)
    except:
        os.unlink(path)
        raise
    return path


def read_file_content(path: str) -> str:
    """Read file content, normalizing line endings."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def compare_file_content(path1: str, path2: str) -> bool:
    """Compare content of two files, ignoring line endings."""
    content1 = read_file_content(path1)
    content2 = read_file_content(path2)
    return content1.replace("\r\n", "\n") == content2.replace("\r\n", "\n")
