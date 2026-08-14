import csv
from pathlib import Path
import tempfile
import unittest

from aruco_docking.csv_logger import CsvLogger, FIELDNAMES


class CsvLoggerTest(unittest.TestCase):
    def test_writes_header_and_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "run.csv"
            logger = CsvLogger(str(path))
            logger.write({"state": "STOP", "stop_reason": "reached"})
            logger.close()

            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(list(rows[0]), FIELDNAMES)
            self.assertEqual(rows[0]["state"], "STOP")
            self.assertEqual(rows[0]["stop_reason"], "reached")


if __name__ == "__main__":
    unittest.main()
