import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import av
import numpy as np

from smartcamera.capture import SmartCameraCapture, build_parser, main
from helpers import sample


class CaptureTests(unittest.TestCase):
    def test_cli_rejects_invalid_rates_ports_timeouts_and_conflicting_output(self):
        invalid = [["--fps", value] for value in ("0", "-1", "nan", "inf", "text")]
        invalid += [["--port", value] for value in ("0", "65536", "1.5")]
        invalid += [["--timeout", "0"], ["--output", "video.mkv", "--no-save"]]
        for arguments in invalid:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    build_parser().parse_args(arguments)
                self.assertEqual(result.exception.code, 2)

    def test_cli_passes_runtime_configuration(self):
        with patch("smartcamera.capture.SmartCameraCapture") as camera:
            camera.return_value.save_video = False
            self.assertEqual(main(["--ip", "camera.local", "--port", "4321", "--fps", "12", "--timeout", "2", "--no-save"]), 0)
        camera.assert_called_once_with(ip="camera.local", port=4321, fps=12.0,
                                      output_path=None, save_video=False, timeout=2.0)
        camera.return_value.run.assert_called_once()

    def test_invalid_extension_and_existing_companion_fail_before_connect(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.mkv"
            path.with_suffix(".session.json").write_text("preserve")
            with patch("smartcamera.capture.LimaClient.connect") as connect:
                for output in (str(path), str(Path(directory) / "video.mp4")):
                    with self.subTest(output=output), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as result:
                            main(["--output", output])
                        self.assertEqual(result.exception.code, 2)
            connect.assert_not_called()

    def test_timeout_preserves_native_frame_and_marks_session(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.mkv"
            image = np.random.default_rng(8).integers(0, 256, (48, 64), dtype=np.uint8)
            camera = SmartCameraCapture(fps=1000, output_path=path)
            client = Mock()
            client.take_frame.side_effect = [sample(image, time.perf_counter_ns() - 500_000_000), TimeoutError("camera stopped")]
            with (
                patch("smartcamera.capture.LimaClient", return_value=client),
                patch("smartcamera.capture.cv2.namedWindow"),
                patch("smartcamera.capture.cv2.resizeWindow"),
                patch("smartcamera.capture.cv2.destroyAllWindows") as destroy,
                patch.object(camera, "_preview", return_value=-1),
            ):
                with self.assertRaises(TimeoutError):
                    camera.run()
            client.close.assert_called_once()
            destroy.assert_called_once()
            with av.open(str(path)) as container:
                frames = list(container.decode(video=0))
            self.assertEqual(len(frames), 1)
            np.testing.assert_array_equal(frames[0].to_ndarray(format="gray"), image)
            summary = json.loads(path.with_suffix(".session.json").read_text())
            self.assertEqual(summary["status"], "error")
            self.assertIn("camera stopped", summary["stop_reason"])

    def test_connection_failure_has_session_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failed.mkv"
            with patch("smartcamera.capture.LimaClient") as client:
                client.return_value.connect.side_effect = OSError("unreachable")
                with self.assertRaises(OSError):
                    SmartCameraCapture(output_path=path).run()
                client.return_value.close.assert_called_once()
            summary = json.loads(path.with_suffix(".session.json").read_text())
            self.assertEqual(summary["status"], "error")
            self.assertEqual(summary["frame_count"], 0)

    def test_keyboard_interrupt_finalizes_the_recorded_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "interrupted.mkv"
            camera = SmartCameraCapture(fps=1000, output_path=path)
            image = np.zeros((8, 8), dtype=np.uint8)
            client = Mock()
            client.take_frame.side_effect = [sample(image, time.perf_counter_ns() - 500_000_000), KeyboardInterrupt()]
            with (
                patch("smartcamera.capture.LimaClient", return_value=client),
                patch("smartcamera.capture.cv2.namedWindow"),
                patch("smartcamera.capture.cv2.resizeWindow"),
                patch("smartcamera.capture.cv2.destroyAllWindows"),
                patch.object(camera, "_preview", return_value=-1),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    camera.run()
            summary = json.loads(path.with_suffix(".session.json").read_text())
            self.assertEqual(summary["status"], "interrupted")
            with av.open(str(path)) as container:
                self.assertEqual(len(list(container.decode(video=0))), 1)

    def test_preview_does_not_modify_native_pixels(self):
        image = np.full((720, 960, 3), 90, dtype=np.uint8)
        camera = SmartCameraCapture(save_video=False)
        with (
            patch("smartcamera.capture.cv2.imshow") as show,
            patch("smartcamera.capture.cv2.waitKey", return_value=ord("q")),
        ):
            camera._preview(sample(image, 1_000_000_000), 0)
        np.testing.assert_array_equal(image, np.full_like(image, 90))
        self.assertFalse(np.array_equal(show.call_args.args[1], image))

    def test_no_save_creates_no_recording_and_keyboard_interrupt_closes_client(self):
        camera = SmartCameraCapture(save_video=False)
        client = Mock()
        client.take_frame.side_effect = KeyboardInterrupt()
        with (
            patch("smartcamera.capture.LimaClient", return_value=client),
            patch("smartcamera.capture.SessionRecorder") as recorder,
            patch("smartcamera.capture.cv2.namedWindow"),
            patch("smartcamera.capture.cv2.resizeWindow"),
            patch("smartcamera.capture.cv2.destroyAllWindows"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                camera.run()
        recorder.assert_not_called()
        client.close.assert_called_once()
