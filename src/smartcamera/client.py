"""Bounded LIMA request/response reception and native BMP decoding."""

from dataclasses import dataclass
from datetime import datetime, timezone
import io
import re
import socket
import time

import cv2
import numpy as np
from PIL import Image


COMMAND = '<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>'
MAX_HEADER_BYTES = 2048
MAX_IMAGE_BYTES = 64 * 1024 * 1024
RECV_CHUNK_SIZE = 262144


@dataclass(frozen=True)
class ReceivedFrame:
    image: np.ndarray
    data_length: int
    requested_ns: int
    received_ns: int
    decoded_ns: int
    received_utc: str


class LimaClient:
    """One request at a time, with one deadline for the complete response."""

    def __init__(self, ip, port, timeout=5.0):
        self.ip, self.port, self.timeout = ip, port, timeout
        self.sock = None
        self._buffer = bytearray()
        self._deadline_ns = None

    def connect(self):
        sock = socket.create_connection((self.ip, self.port), timeout=self.timeout)
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        except BaseException:
            sock.close()
            raise
        self.sock = sock
        return sock

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        self._buffer.clear()

    def _set_remaining_timeout(self):
        if self._deadline_ns is None:
            remaining = self.timeout
        else:
            remaining = (self._deadline_ns - time.perf_counter_ns()) / 1e9
            if remaining <= 0:
                raise TimeoutError("LIMA response exceeded the frame deadline.")
        self.sock.settimeout(remaining)

    def recv_header(self):
        while True:
            end = self._buffer.find(b">")
            if end >= 0:
                if end + 1 > MAX_HEADER_BYTES:
                    raise ValueError("LIMA header exceeds 2048 bytes.")
                header = bytes(self._buffer[:end + 1])
                del self._buffer[:end + 1]
                return header
            if len(self._buffer) >= MAX_HEADER_BYTES:
                raise ValueError("LIMA header exceeds 2048 bytes.")
            self._set_remaining_timeout()
            chunk = self.sock.recv(RECV_CHUNK_SIZE)
            if not chunk:
                raise ConnectionError("Socket closed while reading LIMA header.")
            self._buffer.extend(chunk)

    @staticmethod
    def extract_datalen(header):
        match = re.search(rb'\bDATALEN="(\d+)"', header)
        if not match:
            raise ValueError("DATALEN not found in LIMA header.")
        size = int(match.group(1))
        if not 0 < size <= MAX_IMAGE_BYTES:
            raise ValueError("DATALEN must be between 1 byte and 64 MiB.")
        return size

    def recv_exactly(self, size):
        if not 0 < size <= MAX_IMAGE_BYTES:
            raise ValueError("Invalid image length.")
        data = bytearray(size)
        buffered = min(size, len(self._buffer))
        data[:buffered] = self._buffer[:buffered]
        del self._buffer[:buffered]
        view = memoryview(data)
        received = buffered
        while received < size:
            self._set_remaining_timeout()
            count = self.sock.recv_into(
                view[received:], min(RECV_CHUNK_SIZE, size - received)
            )
            if count == 0:
                raise ConnectionError("Socket closed while receiving BMP data.")
            received += count
        return data

    @staticmethod
    def decode_bmp(data):
        if data[:2] != b"BM":
            raise ValueError("Camera response is not a BMP image.")
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None:
            with Image.open(io.BytesIO(data)) as pil:
                if pil.mode == "L":
                    image = np.array(pil)
                else:
                    image = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        if image.dtype != np.uint8 or image.ndim not in (2, 3):
            raise ValueError("Only native 8-bit grayscale or colour BMP is supported.")
        if image.ndim == 3 and image.shape[2] not in (3, 4):
            raise ValueError("Unsupported BMP channel layout.")
        return image

    def take_frame(self):
        if self.sock is None:
            raise RuntimeError("Camera is not connected.")
        requested = time.perf_counter_ns()
        self._deadline_ns = requested + round(self.timeout * 1e9)
        try:
            self._set_remaining_timeout()
            self.sock.sendall(COMMAND.encode("ascii"))
            header = self.recv_header()
            size = self.extract_datalen(header)
            data = self.recv_exactly(size)
            received = time.perf_counter_ns()
            received_utc = datetime.now(timezone.utc).isoformat()
            image = self.decode_bmp(data)
            decoded = time.perf_counter_ns()
            return ReceivedFrame(image, size, requested, received, decoded, received_utc)
        finally:
            self._deadline_ns = None
