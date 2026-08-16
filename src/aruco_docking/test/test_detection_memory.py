import unittest

from aruco_docking.controller import Detection
from aruco_docking.detection_memory import DetectionMemory


class DetectionMemoryTest(unittest.TestCase):
    def setUp(self):
        self.memory = DetectionMemory(timeout_sec=0.75)
        self.detection = Detection(
            horizontal_error=0.1,
            distance_m=1.0,
            marker_id=0,
        )

    def test_empty_memory_returns_none(self):
        self.assertIsNone(self.memory.for_control(1.0))

    def test_recent_detection_is_retained(self):
        self.memory.update(self.detection, 1.0)
        self.memory.update(None, 1.2)
        self.assertIs(self.memory.for_control(1.7), self.detection)

    def test_expired_detection_is_discarded(self):
        self.memory.update(self.detection, 1.0)
        self.assertIsNone(self.memory.for_control(1.751))

    def test_time_reset_discards_old_detection(self):
        self.memory.update(self.detection, 10.0)
        self.assertIsNone(self.memory.for_control(1.0))

    def test_negative_timeout_is_rejected(self):
        with self.assertRaises(ValueError):
            DetectionMemory(timeout_sec=-0.1)


if __name__ == "__main__":
    unittest.main()
