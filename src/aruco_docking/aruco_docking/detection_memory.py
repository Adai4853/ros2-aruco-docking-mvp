"""Short, time-bounded memory for intermittent visual detections."""

from typing import Optional

from .controller import Detection


class DetectionMemory:
    """Keep the last valid detection briefly to smooth occasional missed frames."""

    def __init__(self, timeout_sec: float) -> None:
        if timeout_sec < 0.0:
            raise ValueError("timeout_sec must be non-negative")
        self.timeout_sec = timeout_sec
        self._detection: Optional[Detection] = None
        self._seen_sec: Optional[float] = None

    def update(self, detection: Optional[Detection], now_sec: float) -> None:
        if detection is not None:
            self._detection = detection
            self._seen_sec = now_sec

    def for_control(self, now_sec: float) -> Optional[Detection]:
        if self._detection is None or self._seen_sec is None:
            return None
        age_sec = now_sec - self._seen_sec
        if age_sec < 0.0 or age_sec > self.timeout_sec:
            return None
        return self._detection
