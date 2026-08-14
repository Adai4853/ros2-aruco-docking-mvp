"""OpenCV ArUco marker detection and metric distance estimation."""

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass(frozen=True)
class MarkerObservation:
    marker_id: int
    center_x_px: float
    horizontal_error: float
    distance_m: float


class ArucoDetector:
    def __init__(self, dictionary_name: str, marker_id: int, marker_size_m: float):
        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"Unknown ArUco dictionary: {dictionary_name}")
        self.marker_id = marker_id
        self.marker_size_m = marker_size_m
        dictionary_id = getattr(cv2.aruco, dictionary_name)
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        if hasattr(cv2.aruco, "DetectorParameters"):
            parameters = cv2.aruco.DetectorParameters()
        else:
            parameters = cv2.aruco.DetectorParameters_create()
        self._detector = (
            cv2.aruco.ArucoDetector(self.dictionary, parameters)
            if hasattr(cv2.aruco, "ArucoDetector")
            else None
        )
        self._parameters = parameters

    def detect(
        self,
        image_bgr: np.ndarray,
        camera_matrix: Optional[np.ndarray],
        distortion: Optional[np.ndarray],
    ) -> Optional[MarkerObservation]:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        if self._detector is not None:
            corners, ids, _ = self._detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray,
                self.dictionary,
                parameters=self._parameters,
            )
        if ids is None:
            return None

        flat_ids = ids.flatten().tolist()
        if self.marker_id not in flat_ids:
            return None
        index = flat_ids.index(self.marker_id)
        marker_corners = np.asarray(corners[index], dtype=np.float64).reshape(4, 2)
        center_x = float(np.mean(marker_corners[:, 0]))
        image_center_x = image_bgr.shape[1] / 2.0
        horizontal_error = (center_x - image_center_x) / image_center_x

        distance_m = self._estimate_distance(
            marker_corners,
            camera_matrix,
            distortion,
        )
        if distance_m is None or distance_m <= 0.0:
            return None
        return MarkerObservation(
            marker_id=self.marker_id,
            center_x_px=center_x,
            horizontal_error=float(horizontal_error),
            distance_m=float(distance_m),
        )

    def _estimate_distance(
        self,
        corners: np.ndarray,
        camera_matrix: Optional[np.ndarray],
        distortion: Optional[np.ndarray],
    ) -> Optional[float]:
        if camera_matrix is None:
            return None
        half = self.marker_size_m / 2.0
        object_points = np.array(
            [
                [-half, half, 0.0],
                [half, half, 0.0],
                [half, -half, 0.0],
                [-half, -half, 0.0],
            ],
            dtype=np.float64,
        )
        distortion = (
            np.zeros((5, 1), dtype=np.float64)
            if distortion is None
            else np.asarray(distortion, dtype=np.float64)
        )
        success, _, translation = cv2.solvePnP(
            object_points,
            corners,
            np.asarray(camera_matrix, dtype=np.float64),
            distortion,
            flags=cv2.SOLVEPNP_IPPE_SQUARE,
        )
        if not success:
            return None
        return float(translation.reshape(3)[2])
