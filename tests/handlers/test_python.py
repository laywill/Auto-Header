"""Tests for Python file handler."""

import os
import pytest
from auto_header import AutoHeader
from auto_header.errors import AutoHeaderError
from tests.utils import get_fixture_path, create_temp_file, read_file_content


def test_python_simple_file():
    """Test processing a simple Python file."""
    fixture_path = get_fixture_path("simple.py")
    temp_path = create_temp_file(read_file_content(fixture_path), ".py")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        assert result == True  # File was modified
        content = read_file_content(temp_path)
        assert "Copyright Example Ltd, UK 2025" in content
        assert '"""A simple Python module' in content  # Original docstring preserved
    finally:
        os.unlink(temp_path)


def test_python_with_existing_header():
    """Test processing a Python file with existing header."""
    fixture_path = get_fixture_path("with_header.py")
    temp_path = create_temp_file(read_file_content(fixture_path), ".py")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        assert result == True  # File was modified (year updated)
        content = read_file_content(temp_path)
        assert "Copyright Example Ltd, UK 2025" in content
        assert "2024" not in content
    finally:
        os.unlink(temp_path)


def test_python_future_imports():
    """Test that __future__ imports are preserved."""
    fixture_path = get_fixture_path("future_imports.py")
    temp_path = create_temp_file(read_file_content(fixture_path), ".py")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert "from __future__" in content.split("Copyright")[0]
    finally:
        os.unlink(temp_path)


def test_python_shebang():
    """Test that shebang is preserved."""
    fixture_path = get_fixture_path("shebang.py")
    temp_path = create_temp_file(read_file_content(fixture_path), ".py")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert content.startswith("#!/usr/bin/env python3\n")
        assert "Copyright Example Ltd, UK 2025" in content
    finally:
        os.unlink(temp_path)


def test_python_type_stub():
    """Test processing a .pyi type stub file."""
    fixture_path = get_fixture_path("stub.pyi")
    temp_path = create_temp_file(read_file_content(fixture_path), ".pyi")

    try:
        manager = AutoHeader("Copyright Example Ltd, UK 2025")
        result = manager.process_file(temp_path)

        content = read_file_content(temp_path)
        assert "Copyright Example Ltd, UK 2025" in content
        assert "from typing import" in content  # Imports preserved
    finally:
        os.unlink(temp_path)


def test_python_invalid_header():
    """Test handling of invalid header content."""
    fixture_path = get_fixture_path("invalid_header.py")
    temp_path = create_temp_file(read_file_content(fixture_path), ".py")

    try:
        manager = AutoHeader("def invalid_header():")  # Invalid header with code
        with pytest.raises(AutoHeaderError) as exc:
            manager.process_file(temp_path)
        assert "contains code-like syntax" in str(exc.value)
    finally:
        os.unlink(temp_path)
