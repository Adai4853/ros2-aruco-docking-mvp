import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[3] / "scripts" / "analyze_runs.py"
SPEC = importlib.util.spec_from_file_location("analyze_runs", MODULE_PATH)
analyze_runs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyze_runs)


class AnalyzeRunsTest(unittest.TestCase):
    def _summarize(self, rows):
        fieldnames = ["timestamp_sec", "marker_found", "distance_m", "stop_reason"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return analyze_runs.summarize(path, target_distance_m=0.35)

    def test_uses_distance_on_reached_row(self):
        result = self._summarize(
            [
                {
                    "timestamp_sec": "1.0",
                    "marker_found": "True",
                    "distance_m": "0.37",
                    "stop_reason": "reached",
                }
            ]
        )
        self.assertAlmostEqual(result["error_m"], 0.02)

    def test_uses_first_stationary_distance_after_blank_reached_row(self):
        result = self._summarize(
            [
                {
                    "timestamp_sec": "1.0",
                    "marker_found": "True",
                    "distance_m": "0.39",
                    "stop_reason": "none",
                },
                {
                    "timestamp_sec": "1.1",
                    "marker_found": "False",
                    "distance_m": "",
                    "stop_reason": "reached",
                },
                {
                    "timestamp_sec": "1.2",
                    "marker_found": "True",
                    "distance_m": "0.37",
                    "stop_reason": "reached",
                },
            ]
        )
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["error_m"], 0.02)


if __name__ == "__main__":
    unittest.main()
