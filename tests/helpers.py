"""Deterministic camera responses and timestamps for hardware-free tests."""

import cv2

from smartcamera.client import ReceivedFrame


class MemorySocket:
    def __init__(self, payload, chunk_size=262144):
        self.payload = bytes(payload)
        self.position = 0
        self.chunk_size = chunk_size
        self.calls = 0
        self.sent = b""
        self.closed = False

    def settimeout(self, value):
        self.timeout = value

    def sendall(self, data):
        self.sent += data
        self.position = 0

    def recv(self, count):
        self.calls += 1
        count = min(count, self.chunk_size)
        result = self.payload[self.position:self.position + count]
        self.position += len(result)
        return result

    def recv_into(self, buffer, count):
        data = self.recv(count)
        buffer[:len(data)] = data
        return len(data)

    def close(self):
        self.closed = True


def bmp_payload(image):
    success, encoded = cv2.imencode(".bmp", image)
    if not success:
        raise RuntimeError("BMP encoding failed")
    data = encoded.tobytes()
    return f'<LIMA DIR="Response" DATALEN="{len(data)}"/>'.encode() + data


def sample(image, received_ns):
    return ReceivedFrame(
        image, image.nbytes, received_ns - 2_000_000,
        received_ns, received_ns + 500_000, "2026-10-20T12:00:00+00:00",
    )
