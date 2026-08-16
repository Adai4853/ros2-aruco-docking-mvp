#!/usr/bin/env python3
"""Summarize one or more docking CSV runs without third-party dependencies."""

import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Dict, List


def load_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def reached_distance(rows: List[Dict[str, str]], reached_index: int):
    """Return the closest recorded distance for the first reached sample."""
    if rows[reached_index]["distance_m"]:
        return float(rows[reached_index]["distance_m"])

    # Detection memory can trigger REACHED between camera frames. Prefer the
    # first stationary measurement after that transition, then fall back to
    # the most recent measurement before it.
    for row in rows[reached_index + 1 :]:
        if row["stop_reason"] != "reached":
            break
        if row["distance_m"]:
            return float(row["distance_m"])
    for row in reversed(rows[:reached_index]):
        if row["distance_m"]:
            return float(row["distance_m"])
    return None


def summarize(path: Path, target_distance_m: float) -> Dict[str, object]:
    rows = load_rows(path)
    if not rows:
        return {
            "file": str(path),
            "success": False,
            "error_m": None,
            "target_loss_stop_sec": None,
        }
    reached_index = next(
        (index for index, row in enumerate(rows) if row["stop_reason"] == "reached"),
        None,
    )
    distance = (
        None if reached_index is None else reached_distance(rows, reached_index)
    )

    loss_latency = None
    target_lost_index = next(
        (
            index
            for index, row in enumerate(rows)
            if row["stop_reason"] == "target_lost"
        ),
        None,
    )
    if target_lost_index is not None:
        visible_rows = [
            row
            for row in rows[:target_lost_index]
            if row["marker_found"].lower() == "true"
        ]
        if visible_rows:
            loss_latency = float(rows[target_lost_index]["timestamp_sec"]) - float(
                visible_rows[-1]["timestamp_sec"]
            )
    return {
        "file": str(path),
        "success": reached_index is not None,
        "error_m": None if distance is None else abs(distance - target_distance_m),
        "target_loss_stop_sec": loss_latency,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("--target-distance", type=float, default=0.35)
    args = parser.parse_args()

    runs = [summarize(path, args.target_distance) for path in args.csv]
    errors = [run["error_m"] for run in runs if run["error_m"] is not None]
    loss_latencies = [
        run["target_loss_stop_sec"]
        for run in runs
        if run["target_loss_stop_sec"] is not None
    ]
    successful = sum(bool(run["success"]) for run in runs)
    print(f"runs: {len(runs)}")
    print(f"successes: {successful}")
    print(f"success_rate: {successful / len(runs) * 100:.1f}%")
    if errors:
        print(f"mean_stop_error_m: {mean(errors):.4f}")
        print(f"max_stop_error_m: {max(errors):.4f}")
    if loss_latencies:
        print(f"mean_target_loss_stop_sec: {mean(loss_latencies):.4f}")
        print(f"max_target_loss_stop_sec: {max(loss_latencies):.4f}")


if __name__ == "__main__":
    main()
