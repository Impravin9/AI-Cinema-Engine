import unittest
from PIL import Image

from video_generation import camera_motion, image_data_uri


class VideoGenerationHelpersTests(unittest.TestCase):
    def test_camera_motion_mapping(self):
        self.assertEqual(camera_motion("slow_push_in"), "dolly_in")
        self.assertEqual(camera_motion("slow_pull_back"), "dolly_out")
        self.assertEqual(camera_motion("unknown"), "none")

    def test_image_reference_is_a_small_jpeg_data_uri(self):
        image = Image.new("RGB", (1280, 720), (120, 80, 40))
        uri = image_data_uri(image)
        self.assertTrue(uri.startswith("data:image/jpeg;base64,"))
        import base64
        payload = base64.b64decode(uri.split(",", 1)[1])
        self.assertLessEqual(len(payload), 245_000)
        self.assertTrue(payload.startswith(b"\xff\xd8"))


if __name__ == "__main__":
    unittest.main()
