import json
import tempfile
import unittest
from pathlib import Path

from asset_library import (
    open_library,
    register_scene_asset,
    save_manifest,
    scene_signature,
    valid_scene_asset,
)


class AssetLibraryTests(unittest.TestCase):
    def test_project_library_is_stable_for_same_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, manifest1 = open_library(tmp, "myscript.txt", "same script")
            second, manifest2 = open_library(tmp, "myscript.txt", "same script")
            self.assertEqual(first, second)
            self.assertEqual(manifest1["project"], manifest2["project"])

    def test_scene_assets_resume_and_signature_invalidates_changed_scene(self):
        scene = {"text": "A historical scene", "queries": ["archive photo"]}
        with tempfile.TemporaryDirectory() as tmp:
            folder, manifest = open_library(tmp, "story.txt", "full script")
            path = folder / "scene_001.jpg"
            path.write_bytes(b"image-placeholder-for-path-existence")
            register_scene_asset(folder, manifest, 0, scene, "CC0 | source")
            self.assertIsNotNone(valid_scene_asset(folder, manifest, 0, scene))
            changed = dict(scene, text="A different scene")
            self.assertIsNone(valid_scene_asset(folder, manifest, 0, changed))
            saved = json.loads((folder / "asset_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["scenes"]["1"]["credit_and_source"], "CC0 | source")


if __name__ == "__main__":
    unittest.main()
