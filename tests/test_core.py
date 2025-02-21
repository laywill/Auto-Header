"""Core functionality tests for Auto-Header."""

import pytest
import os
from pathlib import Path
from typing import Dict, Any
from auto_header import AutoHeader
from auto_header.errors import AutoHeaderError
from tests.utils import get_fixture_path


def test_init_with_empty_header():
    """Test that initialization fails with empty header."""
    with pytest.raises(AutoHeaderError) as exc:
        AutoHeader(header_text="")
    assert "Header text cannot be empty" in str(exc.value)


def test_init_with_valid_header():
    """Test successful initialization."""
    header = "Copyright Example Ltd, UK 2025"
    manager = AutoHeader(header_text=header)
    assert manager.header_text == header
    assert len(manager.handlers) > 0


def test_ignore_patterns():
    """Test that ignore patterns work correctly."""
    manager = AutoHeader(
        header_text="Copyright Example Ltd, UK 2025",
        ignore_patterns=["*.txt", "temp/*"],
    )
    assert manager.should_ignore("test.txt")
    assert manager.should_ignore("temp/file.py")
    assert not manager.should_ignore("src/main.py")


def test_directory_processing():
    """Test processing an entire directory."""
    test_dir = Path(get_fixture_path("simple.py")).parent

    manager = AutoHeader("Copyright Example Ltd, UK 2025")
    stats = manager.process_directory(str(test_dir))

    assert stats["processed"] > 0
    assert stats["modified"] > 0
    assert stats["skipped"] >= 0


def test_error_reporting():
    """Test error reporting functionality."""
    manager = AutoHeader("Copyright Example Ltd, UK 2025")
    report = manager.get_error_report()

    assert "total_errors" in report
    assert "by_level" in report
    assert "errors" in report
