import importlib.metadata

try:
    __version__ = importlib.metadata.version("rsmetacheck")
except importlib.metadata.PackageNotFoundError:
    try:
        import tomllib
        from pathlib import Path
        _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(_pyproject_path, "rb") as _f:
            __version__ = tomllib.load(_f)["tool"]["poetry"]["version"]
    except Exception:
        __version__ = "unknown"

from .detect_pitfalls_main import main
from .cli import cli
