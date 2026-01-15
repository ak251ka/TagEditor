from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_MODELS = {
    "joytag_models": PROJECT_ROOT / "vendor" / "joytag" / "Models.py",
}


def load_models_module(name: str) -> ModuleType:
    try:
        models_py = _MODELS[name]
    except KeyError as e:
        raise KeyError(f"Unknown model module key: {name}") from e

    if not models_py.is_file():
        raise FileNotFoundError(f"Models file not found: {models_py}")

    spec = importlib.util.spec_from_file_location(name, models_py)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for: {models_py}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
