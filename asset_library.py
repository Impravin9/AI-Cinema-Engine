"""Persistent per-script visual asset library for offline-first rendering."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def project_key(script_path: str, script_text: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(script_path).stem).strip("_") or "film"
    digest = hashlib.sha256(script_text.encode("utf-8")).hexdigest()[:10]
    return f"{stem}_{digest}"


def scene_signature(scene: dict[str, Any]) -> str:
    stable = {
        "text": scene.get("text", ""),
        "queries": scene.get("queries", []),
        "gen_prompt": scene.get("gen_prompt", ""),
    }
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def open_library(root: str, script_path: str, script_text: str) -> tuple[Path, dict[str, Any]]:
    folder = Path(root) / project_key(script_path, script_text)
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "asset_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
    else:
        manifest = {}
    manifest.setdefault("version", 1)
    manifest.setdefault("project", folder.name)
    manifest.setdefault("scenes", {})
    return folder, manifest


def save_manifest(folder: Path, manifest: dict[str, Any]) -> None:
    target = folder / "asset_manifest.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)


def scene_asset_path(folder: Path, index: int) -> Path:
    return folder / f"scene_{index + 1:03d}.jpg"


def valid_scene_asset(folder: Path, manifest: dict[str, Any], index: int, scene: dict[str, Any]) -> tuple[Path, dict[str, Any]] | None:
    record = manifest.get("scenes", {}).get(str(index + 1), {})
    path = scene_asset_path(folder, index)
    if not path.is_file() or record.get("signature") != scene_signature(scene):
        return None
    return path, record


def register_scene_asset(
    folder: Path,
    manifest: dict[str, Any],
    index: int,
    scene: dict[str, Any],
    source_credit: str,
) -> Path:
    path = scene_asset_path(folder, index)
    manifest.setdefault("scenes", {})[str(index + 1)] = {
        "file": path.name,
        "signature": scene_signature(scene),
        "credit_and_source": source_credit,
        "selection": "automatic",
    }
    save_manifest(folder, manifest)
    return path
