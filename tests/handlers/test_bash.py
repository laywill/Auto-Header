"""Tests for Bash file handler."""

import os
import pytest
from auto_header import AutoHeader
from tests.utils import get_fixture_path, create_temp_file, read_file_content


def test_bash_shebang():
    """Test processing a bash file with shebang."""
    fixture_path = get_fixture_path("shebang.sh")
    temp_path = create_temp_file(read_file_content(fixture_path), ".sh")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert content.startswith("#!/bin/bash\n")
        assert "Copyright Example Ltd, UK 2025" in content
    finally:
        os.unlink(temp_path)


def test_bash_executable_permissions():
    """Test that executable permissions are preserved."""
    fixture_path = get_fixture_path("executable.sh")
    temp_path = create_temp_file(read_file_content(fixture_path), ".sh")
    os.chmod(temp_path, 0o755)  # Make executable

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        assert os.access(temp_path, os.X_OK)  # Should still be executable
    finally:
        os.unlink(temp_path)


def test_bash_with_settings():
    """Test that shell settings are preserved."""
    fixture_path = get_fixture_path("with_settings.sh")
    temp_path = create_temp_file(read_file_content(fixture_path), ".sh")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert "set -e" in content
        assert "set -u" in content
        assert "IFS=" in content
    finally:
        os.unlink(temp_path)


def test_bash_simple():
    """Test processing a simple bash file."""
    fixture_path = get_fixture_path("simple.sh")
    temp_path = create_temp_file(read_file_content(fixture_path), ".sh")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert "Copyright Example Ltd, UK 2025" in content
        assert 'echo "Simple bash script"' in content
    finally:
        os.unlink(temp_path)


def test_bash_existing_header():
    """Test updating existing header in bash file."""
    fixture_path = get_fixture_path("with_header.sh")
    temp_path = create_temp_file(read_file_content(fixture_path), ".sh")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert "Copyright Example Ltd, UK 2025" in content
        assert "2024" not in content
    finally:
        os.unlink(temp_path)
