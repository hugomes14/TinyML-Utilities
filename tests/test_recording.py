import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import av
import numpy as np

from smartcamera.recording import SessionRecorder
from helpers import sample


class RecordingTests(unittest.TestCase):
    def test_lossless_vfr_timestamps_and_last_frame_duration(self):
        for shape, pixel_format in (((48, 64), "gray"), ((48, 64, 3), "bgr24")):
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "ensaio_á.mkv"
                recorder = SessionRecorder(path, {"target_fps": 20})
                expected = [np.random.default_rng(i).integers(0, 256, shape, dtype=np.uint8) for i in range(3)]
                for image, elapsed in zip(expected, (0, 100_000_000, 370_000_000)):
                    recorder.write(sample(image, 1_000_000_000 + elapsed))
                recorder.close(1_500_000_000)
                with av.open(str(path)) as container:
                    frames = list(container.decode(video=0))
                    self.assertEqual(len(frames), 3)
                    self.assertAlmostEqual(container.duration / av.time_base, 0.5, places=3)
                    self.assertEqual([float(frame.pts * frame.time_base) for frame in frames], [0, 0.1, 0.37])
                    for image, frame in zip(expected, frames):
                        np.testing.assert_array_equal(frame.to_ndarray(format=pixel_format), image)
                summary = json.loads(path.with_suffix(".session.json").read_text(encoding="utf-8"))
                self.assertEqual(summary["frame_count"], 3)
                self.assertEqual(summary["status"], "completed")
                self.assertEqual(summary["elapsed_ns"], 500_000_000)
                self.assertEqual(summary["stages"]["decode"]["mean_ms"], 0.5)
                with path.with_suffix(".frames.csv").open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual([int(row["elapsed_ns"]) for row in rows], [0, 100_000_000, 370_000_000])

    def test_existing_companion_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.mkv"
            companion = path.with_suffix(".frames.csv")
            companion.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                SessionRecorder(path, {})
            self.assertEqual(companion.read_text(encoding="utf-8"), "preserve")
            self.assertFalse(path.exists())

    def test_resolution_change_leaves_previous_frames_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.mkv"
            recorder = SessionRecorder(path, {})
            recorder.write(sample(np.zeros((8, 8), dtype=np.uint8), 1_000_000_000))
            with self.assertRaises(ValueError):
                recorder.write(sample(np.zeros((16, 16), dtype=np.uint8), 1_100_000_000))
            recorder.close(1_200_000_000, "error", "resolution_changed")
            with av.open(str(path)) as container:
                self.assertEqual(len(list(container.decode(video=0))), 1)
            summary = json.loads(path.with_suffix(".session.json").read_text())
            self.assertEqual(summary["stop_reason"], "resolution_changed")

    def test_encode_failure_keeps_last_good_frame_until_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "encode_failure.mkv"
            recorder = SessionRecorder(path, {})
            image = np.zeros((8, 8), dtype=np.uint8)
            recorder.write(sample(image, 1_000_000_000))
            recorder.stream = Mock(wraps=recorder.stream)
            recorder.stream.encode.side_effect = [ValueError("encoder failed"), []]
            with self.assertRaisesRegex(ValueError, "encoder failed"):
                recorder.write(sample(image, 1_100_000_000))
            recorder.close(1_500_000_000, "error", "encoder failed")
            with av.open(str(path)) as container:
                self.assertEqual(len(list(container.decode(video=0))), 1)
                self.assertAlmostEqual(container.duration / av.time_base, 0.5, places=3)
