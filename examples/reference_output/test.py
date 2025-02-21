#!/usr/bin/env python3

# Copyright Example Ltd, UK 2025

"""Minimal Python file demonstrating various syntax elements."""

import os  # Standard import
from sys import argv  # Specific import
import math as m  # Import with alias


class Example:
    """A simple class."""

    def __init__(self, value: int):
        """Constructor."""
        self.value = value

    def method(self) -> str:
        """Returns a string."""
        return f"Value: {self.value}"

    @staticmethod
    def static_method():
        """A static method."""
        pass


def function(x: int) -> int:
    """Standalone function."""
    return x * 2


if __name__ == "__main__":
    e = Example(42)  # Instantiate class
    print(e.method())  # Call method
    print(function(5))  # Call function
