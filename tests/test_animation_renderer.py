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
        self.assertIn('joint("hip_"+label', BLENDER_SOURCE)
        self.assertIn('joint("elbow_"+label', BLENDER_SOURCE)
        self.assertIn('joint("knee_"+label', BLENDER_SOURCE)
        self.assertIn("cycles * 2", BLENDER_SOURCE)
        self.assertIn("Distinct playable poses", BLENDER_SOURCE)
        self.assertIn('if action == "fight":', BLENDER_SOURCE)
        self.assertIn('if action == "kneel":', BLENDER_SOURCE)
        self.assertIn('elif action == "sit":', BLENDER_SOURCE)
        self.assertIn('elif action == "point":', BLENDER_SOURCE)
        self.assertIn('joint("ankle_"+label', BLENDER_SOURCE)
        self.assertIn('joint("head_turn"', BLENDER_SOURCE)
        self.assertIn('cam.data.keyframe_insert(data_path="lens"', BLENDER_SOURCE)
        self.assertIn('env_obj["base_location"]', BLENDER_SOURCE)
        self.assertNotIn("CHARACTER_ROOT", BLENDER_SOURCE)

    def test_hero_is_a_stylized_cartoon_with_expressive_face(self):
        for feature in ("large cartoon face", "sculpted fringe", "eye sparkle",
                        "cheek blush", "rounded boot_", "Facial performance",
                        "Reset every articulated joint"):
            self.assertIn(feature, BLENDER_SOURCE)
        self.assertIn("eye_rigs.append(eye)", BLENDER_SOURCE)
        self.assertIn("mouth_open", BLENDER_SOURCE)

    def test_rig_object_collection_flattens_tuple_records(self):
        self.assertIn("[obj for arm in arm_rigs for obj in arm[:2]]", BLENDER_SOURCE)
        self.assertIn("[obj for leg in leg_rigs for obj in leg[:3]]", BLENDER_SOURCE)

    def test_director_adds_actions_and_camera_metadata(self):
        scenes = direct_plan([
            {"text": "A young man runs through the forest."},
            {"text": "He notices smoke rising above the trees."},
        ])
        self.assertEqual(scenes[0]["action"], "run")
        self.assertEqual(scenes[0]["environment"], "forest")
        self.assertEqual(scenes[1]["action"], "react")
        self.assertEqual(scenes[1]["camera_move"], "push_in")


    def test_environment_upgrade_builds_real_scene_kits(self):
        for token in ("forest undergrowth", "mud plaster hut", "interior table",
                      "river channel", "mountain peak", "battlefield rubble"):
            self.assertIn(token, BLENDER_SOURCE)
        self.assertIn('"interior": []', BLENDER_SOURCE)
        self.assertIn("continuous terrain", BLENDER_SOURCE)
        self.assertIn("else 1280", BLENDER_SOURCE)
        self.assertIn("else 720", BLENDER_SOURCE)
        self.assertIn("taa_render_samples=8 if preview else 32", BLENDER_SOURCE)
        self.assertIn("cam.data.dof.use_dof=True", BLENDER_SOURCE)
        self.assertIn("constant_rate_factor = \"HIGH\"", BLENDER_SOURCE)

    def test_director_detects_indoor_scenes_and_emotion(self):
        scene = direct_plan([{"text": "Inside the palace, the afraid guard kneels."}])[0]
        self.assertEqual(scene["environment"], "interior")
        self.assertEqual(scene["mood"], "fear")
        self.assertEqual(scene["action"], "kneel")

    def test_director_uses_whole_words(self):
        scene = direct_plan([{"text": "The runner stood beside a runway."}])[0]
        self.assertEqual(scene["action"], "observe")


if __name__ == "__main__":
    unittest.main()
