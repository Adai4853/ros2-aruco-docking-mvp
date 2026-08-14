import unittest

from aruco_docking.controller import (
    ControllerConfig,
    Detection,
    DockingController,
    DockingState,
    StopReason,
)


def detected(horizontal_error=0.0, distance_m=1.0):
    return Detection(
        horizontal_error=horizontal_error,
        distance_m=distance_m,
        marker_id=0,
    )


class DockingControllerTest(unittest.TestCase):
    def setUp(self):
        self.controller = DockingController(ControllerConfig())

    def test_no_camera_data_stops(self):
        command = self.controller.compute(None, None, None)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.IMAGE_TIMEOUT)

    def test_initial_no_target_searches(self):
        command = self.controller.compute(None, 0.1, None)
        self.assertEqual(command.state, DockingState.SEARCH)
        self.assertEqual(command.linear_x, 0.0)
        self.assertGreater(command.angular_z, 0.0)

    def test_target_loss_after_detection_stops(self):
        self.controller.compute(detected(), 0.1, None)
        command = self.controller.compute(None, 0.1, None)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.TARGET_LOST)

    def test_large_horizontal_error_aligns_before_approach(self):
        command = self.controller.compute(
            detected(horizontal_error=0.5), 0.1, None
        )
        self.assertEqual(command.state, DockingState.TRACK)
        self.assertEqual(command.linear_x, 0.0)
        self.assertLess(command.angular_z, 0.0)

    def test_aligned_target_moves_forward_with_speed_limit(self):
        command = self.controller.compute(detected(distance_m=3.0), 0.1, None)
        self.assertAlmostEqual(command.linear_x, 0.16)

    def test_target_distance_stops(self):
        command = self.controller.compute(detected(distance_m=0.37), 0.1, None)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.REACHED)

    def test_reached_state_stays_stopped_when_distance_fluctuates(self):
        self.controller.compute(detected(distance_m=0.35), 0.1, None)
        command = self.controller.compute(detected(distance_m=0.80), 0.1, None)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.REACHED)
        self.assertEqual(command.linear_x, 0.0)

    def test_obstacle_has_priority(self):
        command = self.controller.compute(detected(), 0.1, 0.20)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.OBSTACLE)

    def test_stale_image_stops(self):
        command = self.controller.compute(detected(), 0.6, None)
        self.assertEqual(command.state, DockingState.STOP)
        self.assertEqual(command.stop_reason, StopReason.IMAGE_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
