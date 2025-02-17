# Auto-Header
Maintaining up-to-date headers (e.g. Copyright headers) is really boring. This automates it.


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
