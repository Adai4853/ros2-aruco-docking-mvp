"""Pure-Python docking state machine and proportional controller.

This module intentionally has no ROS dependency so its safety behaviour can be
unit tested before a ROS 2 environment is available.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DockingState(str, Enum):
    SEARCH = "SEARCH"
    TRACK = "TRACK"
    STOP = "STOP"


class StopReason(str, Enum):
    NONE = "none"
    REACHED = "reached"
    TARGET_LOST = "target_lost"
    IMAGE_TIMEOUT = "image_timeout"
    OBSTACLE = "obstacle"


@dataclass(frozen=True)
class Detection:
    horizontal_error: float
    distance_m: float
    marker_id: int


@dataclass(frozen=True)
class ControlCommand:
    state: DockingState
    linear_x: float
    angular_z: float
    stop_reason: StopReason = StopReason.NONE


@dataclass
class ControllerConfig:
    target_distance_m: float = 0.35
    distance_tolerance_m: float = 0.03
    align_threshold: float = 0.12
    yaw_kp: float = 1.4
    distance_kp: float = 0.35
    max_linear_speed: float = 0.16
    max_angular_speed: float = 0.8
    search_angular_speed: float = 0.3
    image_timeout_sec: float = 0.5
    obstacle_stop_distance_m: float = 0.28


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


class DockingController:
    """SEARCH/TRACK/STOP controller with fail-safe stop conditions."""

    def __init__(self, config: ControllerConfig) -> None:
        self.config = config
        self.has_seen_target = False
        self.is_docked = False

    def reset(self) -> None:
        """Start a fresh docking attempt."""
        self.has_seen_target = False
        self.is_docked = False

    def compute(
        self,
        detection: Optional[Detection],
        image_age_sec: Optional[float],
        obstacle_distance_m: Optional[float],
    ) -> ControlCommand:
        cfg = self.config

        if image_age_sec is None or image_age_sec > cfg.image_timeout_sec:
            return self._stop(StopReason.IMAGE_TIMEOUT)

        if (
            obstacle_distance_m is not None
            and obstacle_distance_m <= cfg.obstacle_stop_distance_m
        ):
            return self._stop(StopReason.OBSTACLE)

        if self.is_docked:
            return self._stop(StopReason.REACHED)

        if detection is None:
            if self.has_seen_target:
                return self._stop(StopReason.TARGET_LOST)
            return ControlCommand(
                state=DockingState.SEARCH,
                linear_x=0.0,
                angular_z=cfg.search_angular_speed,
            )

        self.has_seen_target = True
        distance_error = detection.distance_m - cfg.target_distance_m
        if distance_error <= cfg.distance_tolerance_m:
            self.is_docked = True
            return self._stop(StopReason.REACHED)

        angular_z = clamp(
            -cfg.yaw_kp * detection.horizontal_error,
            -cfg.max_angular_speed,
            cfg.max_angular_speed,
        )
        linear_x = 0.0
        if abs(detection.horizontal_error) <= cfg.align_threshold:
            linear_x = clamp(
                cfg.distance_kp * distance_error,
                0.0,
                cfg.max_linear_speed,
            )

        return ControlCommand(
            state=DockingState.TRACK,
            linear_x=linear_x,
            angular_z=angular_z,
        )

    @staticmethod
    def _stop(reason: StopReason) -> ControlCommand:
        return ControlCommand(
            state=DockingState.STOP,
            linear_x=0.0,
            angular_z=0.0,
            stop_reason=reason,
        )
