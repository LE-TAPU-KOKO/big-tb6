"""Shared storage for latest chest X-ray path between API and bot."""

import os
from typing import Optional


_LATEST_PATH_FILE = os.path.join(os.path.dirname(__file__), "xray_images", "latest.txt")


def set_latest_xray_path(path: str) -> None:
    os.makedirs(os.path.dirname(_LATEST_PATH_FILE), exist_ok=True)
    with open(_LATEST_PATH_FILE, "w", encoding="utf-8") as f:
        f.write(os.path.basename(path))


def get_latest_xray_path() -> Optional[str]:
    if not os.path.exists(_LATEST_PATH_FILE):
        return None
    try:
        with open(_LATEST_PATH_FILE, "r", encoding="utf-8") as f:
            filename = f.read().strip()
        if not filename:
            return None
        return os.path.join(os.path.dirname(__file__), "xray_images", filename)
    except Exception:
        return None
