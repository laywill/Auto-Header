# Auto-Header

Maintaining up-to-date headers (e.g. Copyright headers) is really boring. This automates it.

[![Tests](https://github.com/laywill/auto-header/actions/workflows/test.yml/badge.svg)](https://github.com/laywill/auto-header/actions/workflows/test.yml)
[![MegaLinter](https://github.com/laywill/auto-header/actions/workflows/mega-linter.yml/badge.svg)](https://github.com/laywill/auto-header/actions/workflows/mega-linter.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/laywill/15b3c888d007ceb1043c9a608b9927bb/raw/coverage-badge.json)](https://github.com/laywill/auto-header/actions/workflows/test.yml)

## Project Structure

```markdown
auto-header/
│
├── src/
│   └── auto_header/
│       ├── __init__.py
│       └── main.py           # Our auto header implementation
│
├── tests/
│   ├── __init__.py
│   └── test_auto_header.py
│
├── .gitignore
├── pyproject.toml           # Modern Python packaging config
├── README.md
└── .pre-commit-hooks.yaml   # Pre-commit hook configuration
```

## Installation and Development

1. Clone the repository:
```bash
git clone git@github.com:yourusername/auto-header.git
cd auto-header
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Running Tests

```bash
pytest
```

Or with coverage:
```bash
pytest --cov=auto_header tests/
```

## Using as a Pre-commit Hook

Add to your project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/yourusername/auto-header
    rev: v0.1.0
    hooks:
      - id: auto-header
        args: [--header, "Copyright Example Ltd, UK 2025"]
```
