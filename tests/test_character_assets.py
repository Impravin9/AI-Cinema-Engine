import tempfile
import unittest
from pathlib import Path

from character_assets import validate_character_asset
from animation_renderer import BLENDER_SOURCE


class CharacterAssetTests(unittest.TestCase):
    def test_rejects_missing_asset(self):
        with self.assertRaises(FileNotFoundError):
            validate_character_asset("missing_character.blend")

    def test_rejects_non_blend_asset(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "character.fbx"
            path.write_bytes(b"x" * 2048)
            with self.assertRaisesRegex(ValueError, r"\.blend"):
                validate_character_asset(path)

    def test_accepts_existing_blend_container(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "character.blend"
            path.write_bytes(b"x" * 2048)
            self.assertEqual(validate_character_asset(path), path.resolve())

    def test_embedded_script_has_optional_asset_import_and_compiles(self):
        self.assertIn("bpy.data.libraries.load", BLENDER_SOURCE)
        self.assertIn("procedural_character_objects", BLENDER_SOURCE)
        self.assertIn("character_asset = args[5]", BLENDER_SOURCE)
        compile(BLENDER_SOURCE, "<embedded_blender_scene>", "exec")


if __name__ == "__main__":
    unittest.main()
