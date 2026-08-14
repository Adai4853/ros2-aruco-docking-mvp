#!/usr/bin/env python3
"""Generate the exact ArUco PNG used by the Gazebo model."""

import argparse
from pathlib import Path

import cv2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictionary", default="DICT_4X4_50")
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--pixels", type=int, default=600)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "src/aruco_docking/models/aruco_marker/materials/textures/marker.png"
        ),
    )
    args = parser.parse_args()

    if not hasattr(cv2.aruco, args.dictionary):
        raise SystemExit(f"Unknown ArUco dictionary: {args.dictionary}")
    dictionary = cv2.aruco.getPredefinedDictionary(
        getattr(cv2.aruco, args.dictionary)
    )
    if hasattr(cv2.aruco, "generateImageMarker"):
        marker = cv2.aruco.generateImageMarker(dictionary, args.id, args.pixels)
    else:
        marker = cv2.aruco.drawMarker(dictionary, args.id, args.pixels)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), marker):
        raise SystemExit(f"Could not write {args.output}")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
