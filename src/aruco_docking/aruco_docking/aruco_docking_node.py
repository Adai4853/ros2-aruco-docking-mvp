"""ROS 2 node for ArUco-guided TurtleBot3 docking."""

import math
from typing import Optional

import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, LaserScan

from .aruco_detector import ArucoDetector
from .controller import ControllerConfig, Detection, DockingController
from .csv_logger import CsvLogger


class ArucoDockingNode(Node):
    def __init__(self) -> None:
        super().__init__("aruco_docking_node")
        self._declare_parameters()

        config = ControllerConfig(
            target_distance_m=self._param("target_distance_m"),
            distance_tolerance_m=self._param("distance_tolerance_m"),
            align_threshold=self._param("align_threshold"),
            yaw_kp=self._param("yaw_kp"),
            distance_kp=self._param("distance_kp"),
            max_linear_speed=self._param("max_linear_speed"),
            max_angular_speed=self._param("max_angular_speed"),
            search_angular_speed=self._param("search_angular_speed"),
            image_timeout_sec=self._param("image_timeout_sec"),
            obstacle_stop_distance_m=self._param("obstacle_stop_distance_m"),
        )
        self._controller = DockingController(config)
        self._detector = ArucoDetector(
            self._param("aruco_dictionary"),
            self._param("marker_id"),
            self._param("marker_size_m"),
        )
        self._bridge = CvBridge()
        self._camera_matrix: Optional[np.ndarray] = None
        self._distortion: Optional[np.ndarray] = None
        self._detection: Optional[Detection] = None
        self._last_image_sec: Optional[float] = None
        self._front_obstacle_m: Optional[float] = None
        self._last_state = None
        self._last_reason = None

        self._logger = CsvLogger(self._param("csv_path"))
        self._publisher = self.create_publisher(
            Twist,
            self._param("cmd_vel_topic"),
            10,
        )
        self.create_subscription(
            CameraInfo,
            self._param("camera_info_topic"),
            self._on_camera_info,
            10,
        )
        self.create_subscription(
            Image,
            self._param("image_topic"),
            self._on_image,
            10,
        )
        if self._param("use_laser"):
            self.create_subscription(
                LaserScan,
                self._param("scan_topic"),
                self._on_scan,
                10,
            )

        rate_hz = float(self._param("control_rate_hz"))
        self.create_timer(1.0 / rate_hz, self._control_step)
        self.get_logger().info("ArUco docking node started; waiting for camera data")

    def _declare_parameters(self) -> None:
        defaults = {
            "image_topic": "/camera/image_raw",
            "camera_info_topic": "/camera/camera_info",
            "cmd_vel_topic": "/cmd_vel",
            "scan_topic": "/scan",
            "aruco_dictionary": "DICT_4X4_50",
            "marker_id": 0,
            "marker_size_m": 0.15,
            "target_distance_m": 0.35,
            "distance_tolerance_m": 0.03,
            "align_threshold": 0.12,
            "yaw_kp": 1.4,
            "distance_kp": 0.35,
            "max_linear_speed": 0.16,
            "max_angular_speed": 0.8,
            "search_angular_speed": 0.3,
            "image_timeout_sec": 0.5,
            "obstacle_stop_distance_m": 0.28,
            "front_sector_degrees": 30.0,
            "control_rate_hz": 10.0,
            "use_laser": True,
            "csv_path": "data/docking_run.csv",
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

    def _param(self, name: str):
        return self.get_parameter(name).value

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def _on_camera_info(self, message: CameraInfo) -> None:
        self._camera_matrix = np.asarray(message.k, dtype=np.float64).reshape(3, 3)
        self._distortion = np.asarray(message.d, dtype=np.float64)

    def _on_image(self, message: Image) -> None:
        self._last_image_sec = self._now_sec()
        try:
            image = self._bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
            observation = self._detector.detect(
                image,
                self._camera_matrix,
                self._distortion,
            )
            self._detection = (
                None
                if observation is None
                else Detection(
                    horizontal_error=observation.horizontal_error,
                    distance_m=observation.distance_m,
                    marker_id=observation.marker_id,
                )
            )
        except Exception as error:  # Keep control timer alive and fail safe.
            self._detection = None
            self.get_logger().error(f"Image processing failed: {error}")

    def _on_scan(self, message: LaserScan) -> None:
        half_sector = math.radians(float(self._param("front_sector_degrees"))) / 2.0
        front_ranges = []
        for index, distance in enumerate(message.ranges):
            angle = message.angle_min + index * message.angle_increment
            wrapped_angle = math.atan2(math.sin(angle), math.cos(angle))
            if (
                abs(wrapped_angle) <= half_sector
                and math.isfinite(distance)
                and message.range_min <= distance <= message.range_max
            ):
                front_ranges.append(float(distance))
        self._front_obstacle_m = min(front_ranges) if front_ranges else None

    def _control_step(self) -> None:
        now = self._now_sec()
        image_age = None if self._last_image_sec is None else now - self._last_image_sec
        command = self._controller.compute(
            self._detection,
            image_age,
            self._front_obstacle_m,
        )

        twist = Twist()
        twist.linear.x = command.linear_x
        twist.angular.z = command.angular_z
        self._publisher.publish(twist)

        if command.state != self._last_state or command.stop_reason != self._last_reason:
            self.get_logger().info(
                f"state={command.state.value} reason={command.stop_reason.value} "
                f"linear={command.linear_x:.3f} angular={command.angular_z:.3f}"
            )
            self._last_state = command.state
            self._last_reason = command.stop_reason

        detection = self._detection
        self._logger.write(
            {
                "timestamp_sec": f"{now:.3f}",
                "state": command.state.value,
                "marker_found": detection is not None,
                "marker_id": "" if detection is None else detection.marker_id,
                "horizontal_error": (
                    "" if detection is None else f"{detection.horizontal_error:.6f}"
                ),
                "distance_m": "" if detection is None else f"{detection.distance_m:.6f}",
                "front_obstacle_m": (
                    ""
                    if self._front_obstacle_m is None
                    else f"{self._front_obstacle_m:.6f}"
                ),
                "linear_x": f"{command.linear_x:.6f}",
                "angular_z": f"{command.angular_z:.6f}",
                "stop_reason": command.stop_reason.value,
            }
        )

    def destroy_node(self) -> bool:
        self._publisher.publish(Twist())
        self._logger.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ArucoDockingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
