from __future__ import annotations

import shutil
from pathlib import Path


def pytest_sessionfinish(session, exitstatus) -> None:  # type: ignore[no-untyped-def]
    root = Path(__file__).resolve().parent
    for base in (root, root / "src", root / "tests"):
        cache_dir = base / "__pycache__"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        if base.exists():
            for nested_cache in base.rglob("__pycache__"):
                shutil.rmtree(nested_cache, ignore_errors=True)
