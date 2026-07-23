"""Small runtime helpers shared by the experiment entry points."""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar


T = TypeVar("T")
__all__ = ["loop_func", "save_log"]


def loop_func(
    func: Callable[..., T],
    all_poi_names: Iterable[str],
    **kwargs: Any,
) -> list[T]:
    """Run ``func`` once for every POI name and return the collected results.

    The POI name is passed as the first positional argument, and additional
    keyword arguments are shared by all runs.
    Exceptions are intentionally allowed to propagate so a failed experiment
    cannot be mistaken for a successful one.
    """
    if not callable(func):
        raise TypeError("func must be callable")
    if isinstance(all_poi_names, (str, bytes)):
        raise TypeError("all_poi_names must be an iterable of names, not a string")

    return [func(poi_name, **kwargs) for poi_name in all_poi_names]


class _Tee:
    """Write text to both the original stream and a log file."""

    def __init__(self, console: Any, log_file: Any) -> None:
        self.console = console
        self.log_file = log_file

    def write(self, text: str) -> int:
        self.console.write(text)
        self.log_file.write(text)
        return len(text)

    def flush(self) -> None:
        self.console.flush()
        self.log_file.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.console, name)


_open_log_files: list[Any] = []


def _close_log_files() -> None:
    for log_file in _open_log_files:
        if not log_file.closed:
            log_file.flush()
            log_file.close()


atexit.register(_close_log_files)


def save_log(file_path: str | os.PathLike[str], file_name: str) -> str:
    """Mirror subsequent stdout and stderr output to a UTF-8 log file."""
    log_dir = Path(file_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file_name).suffix
    final_name = file_name if suffix else f"{file_name}.log"
    log_path = log_dir / final_name
    log_file = log_path.open("a", encoding="utf-8", buffering=1)
    _open_log_files.append(log_file)

    sys.stdout = _Tee(sys.__stdout__, log_file)
    sys.stderr = _Tee(sys.__stderr__, log_file)
    return str(log_path)
