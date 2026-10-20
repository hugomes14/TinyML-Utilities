"""Smoke-test the relocated GUI with a real temporary video, without a display."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication

from smartcamera.frame_grabber import VideoFrameGrabber


class FrameGrabberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_video_navigation_and_unicode_frame_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video_path = root / "example.mp4"
            writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 5, (64, 48))
            self.assertTrue(writer.isOpened(), "mp4v codec must be available")
            try:
                for value in (30, 100, 200):
                    writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
            finally:
                writer.release()

            frames_dir = root / "extração"
            window = VideoFrameGrabber(videos_dir=root, frames_dir=frames_dir)
            try:
                with patch("smartcamera.frame_grabber.QFileDialog.getOpenFileName", return_value=(str(video_path), "")) as open_dialog:
                    window.open_video()
                self.assertEqual(open_dialog.call_args.args[2], str(root))
                self.assertEqual(window.total_frames, 3)
                window.next_frame()
                self.assertEqual(window.current_frame, 1)
                expected = window.current_image.copy()
                output = frames_dir / "fotograma_á.png"
                with (
                    patch("smartcamera.frame_grabber.QFileDialog.getSaveFileName", return_value=(str(output), "")) as save_dialog,
                    patch("smartcamera.frame_grabber.QMessageBox.information"),
                ):
                    window.capture_frame()
                suggested = Path(save_dialog.call_args.args[2])
                self.assertEqual(suggested, frames_dir / "example_frame_2.png")
                saved = cv2.imdecode(np.fromfile(output, dtype=np.uint8), cv2.IMREAD_COLOR)
                np.testing.assert_array_equal(saved, expected)
                self.assertEqual(saved.shape, (48, 64, 3))
                window.previous_frame()
                self.assertEqual(window.current_frame, 0)
            finally:
                cap = window.cap
                window.close()
            self.assertFalse(cap.isOpened())


if __name__ == "__main__":
    unittest.main()
