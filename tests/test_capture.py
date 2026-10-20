"""Exercise capture configuration and resource handling without camera hardware."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from smartcamera.capture import COMMAND, SmartCameraStableFPS, build_parser, main


class FragmentedSocket:
    """Return short reads, including mid-header and mid-image boundaries."""

    def __init__(self, payload):
        self.payload = bytearray(payload)
        self.sent = b""
        self.closed = False

    def close(self):
        self.closed = True

    def sendall(self, data):
        self.sent += data

    def recv(self, count):
        count = min(count, 3, len(self.payload))
        result = bytes(self.payload[:count])
        del self.payload[:count]
        return result

    def recv_into(self, buffer, count):
        data = self.recv(count)
        buffer[:len(data)] = data
        return len(data)


class CaptureTests(unittest.TestCase):
    def test_configurable_connection_and_recording_rate(self):
        camera = SmartCameraStableFPS(ip="camera.local", port=1234, fps=7.5, save_video=False)
        with patch("smartcamera.capture.socket.socket") as create_socket:
            sock = camera.connect()
        sock.connect.assert_called_once_with(("camera.local", 1234))
        self.assertEqual(camera.fps, 7.5)
        self.assertAlmostEqual(camera.frame_interval, 1 / 7.5)
        self.assertIs(sock, create_socket.return_value)

    def test_fragmented_lima_bmp_round_trip(self):
        expected = np.full((4, 6, 3), (10, 100, 200), dtype=np.uint8)
        success, encoded = cv2.imencode(".bmp", expected)
        self.assertTrue(success)
        image = encoded.tobytes()
        header = f'<LIMA DIR="Response" DATALEN="{len(image)}"/>'.encode("ascii")
        sock = FragmentedSocket(header + image)
        frame, size = SmartCameraStableFPS(save_video=False).take_frame(sock)
        self.assertEqual(size, len(image))
        self.assertEqual(sock.sent, COMMAND.encode("ascii"))
        np.testing.assert_array_equal(frame, expected)

    def test_truncated_image_fails_instead_of_hanging(self):
        with self.assertRaises(ConnectionError):
            SmartCameraStableFPS(save_video=False).recv_exactly(FragmentedSocket(b"123"), 10)

    def test_capture_records_a_frame_at_the_configured_rate(self):
        frame = np.full((4, 6, 3), 90, dtype=np.uint8)
        success, encoded = cv2.imencode(".bmp", frame)
        self.assertTrue(success)
        image = encoded.tobytes()
        sock = FragmentedSocket(f'<LIMA DATALEN="{len(image)}"/>'.encode() + image)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "capture.mp4"
            camera = SmartCameraStableFPS(fps=7.5, output_path=output)
            with (
                patch.object(camera, "connect", return_value=sock),
                patch("smartcamera.capture.cv2.namedWindow"),
                patch("smartcamera.capture.cv2.resizeWindow"),
                patch("smartcamera.capture.cv2.imshow"),
                patch("smartcamera.capture.cv2.waitKey", return_value=ord("q")),
                patch("smartcamera.capture.cv2.destroyAllWindows"),
            ):
                camera.run()
            self.assertTrue(sock.closed)
            self.assertFalse(camera.video_writer.isOpened())
            video = cv2.VideoCapture(str(output))
            try:
                success, recorded = video.read()
                self.assertTrue(success)
                self.assertEqual(recorded.shape, (720, 960, 3))
                self.assertAlmostEqual(video.get(cv2.CAP_PROP_FPS), 7.5)
            finally:
                video.release()

    def test_missing_length_fails(self):
        with self.assertRaisesRegex(ValueError, "DATALEN"):
            SmartCameraStableFPS(save_video=False).extract_datalen(b"<LIMA/>")

    def test_failed_connect_closes_socket(self):
        with patch("smartcamera.capture.socket.socket") as create_socket:
            sock = create_socket.return_value
            sock.connect.side_effect = OSError("connection failed")
            with self.assertRaises(OSError):
                SmartCameraStableFPS(save_video=False).connect()
        sock.close.assert_called_once()

    def test_initialization_failure_closes_socket_and_writer(self):
        camera = SmartCameraStableFPS()
        sock, writer = Mock(), Mock()
        writer.isOpened.return_value = False
        with tempfile.TemporaryDirectory() as directory:
            camera.output_path = Path(directory) / "nested" / "video.mp4"
            with (
                patch.object(camera, "connect", return_value=sock),
                patch("smartcamera.capture.cv2.namedWindow"),
                patch("smartcamera.capture.cv2.resizeWindow"),
                patch("smartcamera.capture.cv2.destroyAllWindows") as destroy,
                patch("smartcamera.capture.cv2.VideoWriter", return_value=writer),
            ):
                with self.assertRaisesRegex(RuntimeError, "video writer"):
                    camera.run()
                self.assertTrue(camera.output_path.parent.is_dir())
        sock.close.assert_called_once()
        writer.release.assert_called_once()
        destroy.assert_called_once()

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing.mp4"
            output.write_bytes(b"preserve this video")
            camera = SmartCameraStableFPS(output_path=output)
            with patch("smartcamera.capture.cv2.VideoWriter") as writer:
                with self.assertRaises(FileExistsError):
                    camera.init_video_writer()
            writer.assert_not_called()
            self.assertEqual(output.read_bytes(), b"preserve this video")
            with patch.object(SmartCameraStableFPS, "run") as run:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exit_status:
                        main(["--output", str(output)])
            self.assertEqual(exit_status.exception.code, 2)
            run.assert_not_called()

    def test_cli_rejects_invalid_rates_ports_and_conflicting_output(self):
        invalid = [
            ["--fps", value] for value in ("0", "-1", "nan", "inf", "text")
        ] + [
            ["--port", value] for value in ("0", "65536", "1.5")
        ] + [["--output", "video.mp4", "--no-save"]]
        for arguments in invalid:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_status:
                    build_parser().parse_args(arguments)
                self.assertEqual(exit_status.exception.code, 2)

    def test_cli_passes_configuration_without_starting_real_capture(self):
        with patch("smartcamera.capture.SmartCameraStableFPS") as camera:
            camera.return_value.save_video = False
            self.assertEqual(main(["--ip", "camera.local", "--port", "4321", "--fps", "12", "--no-save"]), 0)
        camera.assert_called_once_with(
            ip="camera.local", port=4321, fps=12.0, output_path=None, save_video=False,
        )
        camera.return_value.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
