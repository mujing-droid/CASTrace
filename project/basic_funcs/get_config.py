"""Load and validate experiment metadata."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


_PROJECT_DIR = Path(__file__).resolve().parents[1]
__all__ = [
    "get_config_gt",
    "get_config_metadata",
    "get_config_poiEs",
    "get_config_windows",
    "set_config_path",
]
_config_path = Path(
    os.environ.get("APT_CONFIG", _PROJECT_DIR / "config.json")
).expanduser()


def set_config_path(file_path: str | os.PathLike[str]) -> None:
    """Select a configuration file for subsequent accessor calls."""
    global _config_path
    _config_path = Path(file_path).expanduser()
    _load_config.cache_clear()


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    if not _config_path.is_file():
        raise FileNotFoundError(
            f"Experiment configuration not found: {_config_path}. "
            "Copy project/config.example.json to project/config.json and edit it."
        )

    with _config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise ValueError("The experiment configuration must be a JSON object")
    return config


def _get_mapping(name: str) -> dict[str, Any]:
    value = _load_config().get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"Configuration field {name!r} must be an object")
    return value


def get_config_gt() -> dict[str, list[tuple[Any, ...]]]:
    """Return ground-truth event pairs keyed by POI name."""
    result: dict[str, list[tuple[Any, ...]]] = {}
    for poi_name, events in _get_mapping("ground_truth").items():
        if not isinstance(events, list):
            raise ValueError(f"ground_truth[{poi_name!r}] must be a list")
        converted_events = []
        for event in events:
            if not isinstance(event, (list, tuple)) or len(event) < 2:
                raise ValueError(
                    f"Each ground-truth event for {poi_name!r} needs at least two items"
                )
            converted_events.append(tuple(event))
        result[poi_name] = converted_events
    return result


def get_config_poiEs() -> dict[str, tuple[Any, ...]]:
    """Return the point-of-interest event ``(source, target, key)`` per case."""
    result: dict[str, tuple[Any, ...]] = {}
    for poi_name, event in _get_mapping("poi_events").items():
        if not isinstance(event, (list, tuple)) or len(event) < 3:
            raise ValueError(
                f"poi_events[{poi_name!r}] must contain source, target, and edge key"
            )
        result[poi_name] = tuple(event)
    return result


def get_config_windows() -> dict[str, int]:
    """Return the number of time windows configured for each POI."""
    result: dict[str, int] = {}
    for poi_name, count in _get_mapping("windows").items():
        count = int(count)
        if count <= 0:
            raise ValueError(f"windows[{poi_name!r}] must be greater than zero")
        result[poi_name] = count
    return result


def get_config_metadata() -> dict[str, Any]:
    """Return optional non-event metadata from the configuration."""
    metadata = _load_config().get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("Configuration field 'metadata' must be an object")
    return metadata
