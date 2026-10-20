import unittest
from unittest.mock import Mock, patch

import numpy as np

from smartcamera.client import COMMAND, LimaClient, MAX_IMAGE_BYTES
from helpers import bmp_payload, MemorySocket


class ClientTests(unittest.TestCase):
    def test_fragmented_and_coalesced_responses_preserve_native_pixels(self):
        for shape in ((48, 64), (48, 64, 3)):
            expected = np.random.default_rng(3).integers(0, 256, shape, dtype=np.uint8)
            for chunk_size in (3, 262144):
                with self.subTest(shape=shape, chunk_size=chunk_size):
                    sock = MemorySocket(bmp_payload(expected), chunk_size)
                    client = LimaClient("camera", 33040)
                    client.sock = sock
                    result = client.take_frame()
                    np.testing.assert_array_equal(result.image, expected)
                    self.assertEqual(sock.sent, COMMAND.encode("ascii"))
                    self.assertLessEqual(result.requested_ns, result.received_ns)
                    self.assertLessEqual(result.received_ns, result.decoded_ns)
                    if chunk_size == 262144:
                        self.assertEqual(sock.calls, 1)

    def test_truncated_response_raises(self):
        client = LimaClient("camera", 33040)
        client.sock = MemorySocket(b'<LIMA DATALEN="100"/>short', 3)
        with self.assertRaises(ConnectionError):
            client.take_frame()

    def test_invalid_header_and_lengths_are_bounded(self):
        for header in (b"<LIMA/>", b'<LIMA DATALEN="0"/>', f'<LIMA DATALEN="{MAX_IMAGE_BYTES + 1}"/>'.encode()):
            with self.subTest(header=header), self.assertRaises(ValueError):
                LimaClient.extract_datalen(header)
        client = LimaClient("camera", 33040)
        client.sock = MemorySocket(b"x" * 2049 + b">")
        with self.assertRaises(ValueError):
            client.recv_header()

    def test_response_has_one_total_deadline(self):
        client = LimaClient("camera", 33040, timeout=1)
        client.sock = MemorySocket(bmp_payload(np.zeros((4, 4), dtype=np.uint8)))
        with patch("smartcamera.client.time.perf_counter_ns", side_effect=[0, 0, 2_000_000_000]):
            with self.assertRaises(TimeoutError):
                client.take_frame()
        self.assertEqual(client.sock.calls, 0)

    def test_socket_setup_failure_closes_connection(self):
        sock = Mock()
        sock.setsockopt.side_effect = OSError("setup failed")
        with patch("smartcamera.client.socket.create_connection", return_value=sock) as connect:
            with self.assertRaises(OSError):
                LimaClient("camera.local", 4321, 2).connect()
        connect.assert_called_once_with(("camera.local", 4321), timeout=2)
        sock.close.assert_called_once()

    def test_non_bmp_response_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "BMP"):
            LimaClient.decode_bmp(b"not an image")
