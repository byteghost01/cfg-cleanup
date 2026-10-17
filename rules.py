"""Which files the clean-up route may delete. Pure (no ComfyUI imports), so the CF Gallery tests and
its mock ComfyUI use exactly these rules.

- `type: "output"`: only the app's own files — the name starts with `cfg_` (its `filename_prefix`,
  D-020) — anywhere under ComfyUI's output folder.
- `type: "temp"`: any image in ComfyUI's temp folder (scratch space ComfyUI itself wipes on start;
  the sampler leaves a preview copy there for every job).
- Image files only; no path tricks (`..`, absolute paths, symlinks out of the folder).
"""
from __future__ import annotations

import os

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
APP_PREFIX = "cfg_"


def target(item: object, dirs: dict[str, str]) -> str | None:
    """The absolute path to delete for `{"filename", "subfolder", "type"}`, or None if not allowed."""
    if not isinstance(item, dict):
        return None
    kind, name, sub = item.get("type"), item.get("filename"), item.get("subfolder") or ""
    if kind not in dirs or not isinstance(name, str) or not isinstance(sub, str):
        return None
    if not name or os.path.basename(name) != name or name in (".", ".."):
        return None
    if os.path.splitext(name)[1].lower() not in IMAGE_EXTS:
        return None
    if kind == "output" and not name.startswith(APP_PREFIX):
        return None
    base = os.path.realpath(dirs[kind])
    path = os.path.realpath(os.path.join(base, sub, name))
    if os.path.commonpath([base, path]) != base or path == base:
        return None
    return path
