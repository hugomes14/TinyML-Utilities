"""Exercise VFR navigation, cached export, and failure handling offscreen."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QApplication

from smartcamera.frame_grabber import VideoFrameGrabber
from smartcamera.recording import SessionRecorder
from smartcamera.video import VideoReader
from helpers import sample


def create_video(path):
    images = [np.random.default_rng(i).integers(0, 256, (48, 64), dtype=np.uint8) for i in range(3)]
    recorder = SessionRecorder(path, {})
    for image, elapsed in zip(images, (0, 100_000_000, 370_000_000)):
        recorder.write(sample(image, 1_000_000_000 + elapsed))
    recorder.close(1_500_000_000)
    return images


def open_video(window, path):
    with patch("smartcamera.frame_grabber.QFileDialog.getOpenFileName", return_value=(str(path), "")):
        window.open_video()


class FrameGrabberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_vfr_navigation_and_cached_unicode_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "example.mkv"
            images = create_video(path)
            window = VideoFrameGrabber(root, root / "extração")
            try:
                open_video(window, path)
                self.assertEqual(window.total_frames, 3)
                window.show_frame(2)
                self.assertIn("0.370s", window.info_label.text())
                window.previous_frame()
                self.assertEqual(window.current_frame, 1)
                np.testing.assert_array_equal(window.current_image, images[1])
                output = root / "extração" / "fotograma_á.png"
                with (
                    patch.object(window.reader, "read", wraps=window.reader.read) as read,
                    patch("smartcamera.frame_grabber.QFileDialog.getSaveFileName", return_value=(str(output), "")) as dialog,
                    patch("smartcamera.frame_grabber.QMessageBox.information"),
                ):
                    window.resizeEvent(QResizeEvent(QSize(1100, 750), QSize(1000, 700)))
                    window.capture_frame()
                    read.assert_not_called()
                self.assertEqual(Path(dialog.call_args.args[2]).name, "example_frame_2.png")
                saved = cv2.imdecode(np.fromfile(output, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                np.testing.assert_array_equal(saved, images[1])
            finally:
                reader = window.reader
                window.close()
            self.assertTrue(reader.closed)

    def test_failed_open_preserves_current_video(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.mkv"
            images = create_video(path)
            window = VideoFrameGrabber()
            try:
                open_video(window, path)
                original = window.reader
                with (
                    patch("smartcamera.frame_grabber.VideoReader", side_effect=ValueError("invalid video")),
                    patch("smartcamera.frame_grabber.QMessageBox.critical"),
                ):
                    open_video(window, "invalid.mkv")
                self.assertIs(window.reader, original)
                self.assertFalse(original.closed)
                np.testing.assert_array_equal(window.current_image, images[0])
            finally:
                window.close()

    def test_failed_navigation_keeps_visible_frame_and_slider(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.mkv"
            images = create_video(path)
            window = VideoFrameGrabber()
            try:
                open_video(window, path)
                with (
                    patch.object(window.reader, "read", side_effect=ValueError("decode failed")),
                    patch("smartcamera.frame_grabber.QMessageBox.warning"),
                ):
                    window.slider.setValue(2)
                self.assertEqual(window.current_frame, 0)
                self.assertEqual(window.slider.value(), 0)
                np.testing.assert_array_equal(window.current_image, images[0])
            finally:
                window.close()

    def test_legacy_mp4_still_opens(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.mp4"
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 5, (64, 48))
            self.assertTrue(writer.isOpened())
            try:
                for value in (30, 100, 200):
                    writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
            finally:
                writer.release()
            reader = VideoReader(path)
            try:
                self.assertEqual(reader.total_frames, 3)
                self.assertAlmostEqual(reader.relative_time(2), 0.4)
                self.assertEqual(reader.read(2).shape, (48, 64, 3))
            finally:
                reader.close()
