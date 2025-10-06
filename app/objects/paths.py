from __future__ import annotations
from pathlib import Path

# Project root (directory containing main.py)
# app/objects/paths.py -> parents[2] = <project_root>
ROOT_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

APP_TITLE = "DataEncap + NFT Desktop"