# Auto-Header

Maintaining up-to-date headers (e.g. Copyright headers) is really boring. This automates it.

[![Tests](https://github.com/laywill/auto-header/actions/workflows/test.yml/badge.svg)](https://github.com/laywill/auto-header/actions/workflows/test.yml)
[![MegaLinter](https://github.com/laywill/auto-header/actions/workflows/mega-linter.yml/badge.svg)](https://github.com/laywill/auto-header/actions/workflows/mega-linter.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/laywill/15b3c888d007ceb1043c9a608b9927bb/raw/coverage-badge.json)](https://github.com/laywill/auto-header/actions/workflows/test.yml)

## Project Structure

```plaintext
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

## Versioning

### Display

Invoking the version command without any arguments will display the current version of the project:

```console
$ hatch version
0.0.1
```

### Updating

You can update the version like so:

```console
$ hatch version "0.1.0"
Old: 0.0.1
New: 0.1.0
```

The scheme option determines the scheme to use for parsing both the existing and new versions. The standard scheme is used by default, which is based on PEP 440.

Rather than setting the version explicitly, you can select the name of a segment used to increment the version:

```console
$ hatch version minor
Old: 0.1.0
New: 0.2.0
```

You can chain multiple segment updates with a comma. For example, if you wanted to release a preview of your project's first major version, you could do:

```console
$ hatch version major,rc
Old: 0.2.0
New: 1.0.0rc0
```

When you want to release the final version, you would do:

```console
$ hatch version release
Old: 1.0.0rc0
New: 1.0.0
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
