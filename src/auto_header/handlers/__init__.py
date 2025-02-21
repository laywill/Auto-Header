# src/auto_header/handlers/__init__.py
from .python import PythonHandler
from .powershell import PowerShellHandler
from .terraform import TerraformHandler
from .bash import BashHandler
from .yaml import YAMLHandler

HANDLERS = [
    PythonHandler,
    PowerShellHandler,
    TerraformHandler,
    BashHandler,
    YAMLHandler,
]
