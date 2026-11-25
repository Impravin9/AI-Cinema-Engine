import unittest

from cinematic_director import direct_plan, direct_scene


class CinematicDirectorTests(unittest.TestCase):
    def test_run_scene_gets_tracking_shot(self):
        scene = direct_scene({"text": "He runs toward the forest."})
        self.assertEqual(scene["action"], "run")
        self.assertEqual(scene["camera_move"], "tracking")
        self.assertEqual(scene["environment"], "forest")

    def test_reaction_scene_gets_close_up(self):
        scene = direct_scene({"text": "He notices smoke rising nearby."})
        self.assertEqual(scene["action"], "react")
        self.assertEqual(scene["shot_type"], "close_up")
        self.assertEqual(scene["mood"], "curiosity")

    def test_explicit_user_direction_is_preserved(self):
        scene = direct_scene({
            "text": "He walks home.",
            "action": "observe",
            "shot_type": "wide",
        })
        self.assertEqual(scene["action"], "observe")
        self.assertEqual(scene["shot_type"], "wide")

    def test_plan_keeps_scene_order_and_count(self):
        scenes = [{"text": "He walks."}, {"text": "He runs."}]
        directed = direct_plan(scenes)
        self.assertEqual(len(directed), 2)
        self.assertEqual([x["action"] for x in directed], ["walk", "run"])
        self.assertEqual([x["shot_index"] for x in directed], [0, 1])

    def test_combat_is_not_misclassified_as_static_fear(self):
        scene = direct_scene({"text": "The soldier attacks and fights the enemy."})
        self.assertEqual(scene["action"], "fight")
        self.assertEqual(scene["environment"], "battlefield")
        self.assertEqual(scene["pace"], "fast")

    def test_kneeling_is_not_a_fall(self):
        scene = direct_scene({"text": "The guard kneels before the king."})
        self.assertEqual(scene["action"], "kneel")

    def test_sitting_and_pointing_get_playable_actions(self):
        self.assertEqual(direct_scene({"text": "She sits beside the fire."})["action"], "sit")
        self.assertEqual(direct_scene({"text": "He points toward the mountains."})["action"], "point")

    def test_scene_change_gets_establishing_transition(self):
        directed = direct_plan([
            {"text": "He walks through the forest."},
            {"text": "He enters the palace hall."},
        ])
        self.assertEqual(directed[1]["transition"], "establishing_cut")

    def test_explicit_transition_is_preserved(self):
        directed = direct_plan([
            {"text": "Forest."},
            {"text": "Palace.", "transition": "match_cut"},
        ])
        self.assertEqual(directed[1]["transition"], "match_cut")


if __name__ == "__main__":
    unittest.main()
