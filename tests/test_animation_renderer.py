import unittest

from animation_renderer import BLENDER_SOURCE, split_script
from cinematic_director import direct_plan


class AnimationRendererTests(unittest.TestCase):
    def test_script_is_split_into_scene_beats(self):
        scenes = split_script("A soldier enters. He looks toward the city! The sky darkens?")
        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0]["text"], "A soldier enters.")
        self.assertEqual(scenes[2]["text"], "The sky darkens?")

    def test_empty_script_fallback_is_predictable(self):
        scenes = split_script("A single scene")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["text"], "A single scene")

    def test_blender_scene_is_procedural_and_offline(self):
        self.assertIn("primitive_uv_sphere_add", BLENDER_SOURCE)
        self.assertIn("primitive_cylinder_add", BLENDER_SOURCE)
        self.assertIn("keyframe_insert", BLENDER_SOURCE)
        self.assertNotIn("requests.get", BLENDER_SOURCE)
        self.assertNotIn("urllib.request", BLENDER_SOURCE)


    def test_embedded_blender_script_compiles_after_rig_upgrade(self):
        compile(BLENDER_SOURCE, "<blender_scene>", "exec")

    def test_character_uses_joint_pivots_and_real_gait(self):
        self.assertIn("hip_L", BLENDER_SOURCE)
        self.assertIn("elbow_L", BLENDER_SOURCE)
        self.assertIn("knee_L", BLENDER_SOURCE)
        self.assertIn("cycles * 2", BLENDER_SOURCE)
        self.assertNotIn("CHARACTER_ROOT", BLENDER_SOURCE)

    def test_director_adds_actions_and_camera_metadata(self):
        scenes = direct_plan([
            {"text": "A young man runs through the forest."},
            {"text": "He notices smoke rising above the trees."},
        ])
        self.assertEqual(scenes[0]["action"], "run")
        self.assertEqual(scenes[0]["environment"], "forest")
        self.assertEqual(scenes[1]["action"], "react")
        self.assertEqual(scenes[1]["camera_move"], "push_in")


if __name__ == "__main__":
    unittest.main()
