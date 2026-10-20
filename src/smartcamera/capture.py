"""Capture and record BMP frames requested from a LIMA smartcamera."""

import argparse
from datetime import datetime
import io
import math
from pathlib import Path
import re
import socket
import time
import logging
import cv2
import numpy as np
from PIL import Image


IP = "192.168.249.197"
PORT = 33040

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

TARGET_FPS = 20

COMMAND = '<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>'

RECV_CHUNK_SIZE = 262144

DEFAULT_OUTPUT_DIR = Path("data/videos/captures")


class SmartCameraStableFPS:
    """Keep the existing capture pacing while allowing runtime configuration."""

    def __init__(self, ip=IP, port=PORT, fps=TARGET_FPS, output_path=None, save_video=True):
        if not ip:
            raise ValueError("Camera IP or hostname must not be empty.")
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535.")
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("FPS must be a finite number greater than zero.")

        self.ip = ip
        self.port = port
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.save_video = save_video
        self.output_path = Path(output_path) if output_path is not None else (
            DEFAULT_OUTPUT_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S_%f}.mp4"
        )
        if self.save_video and self.output_path.suffix.lower() != ".mp4":
            raise ValueError("Capture output must have an .mp4 extension.")

        self.frame_count = 0
        self.start_time = time.perf_counter()
        self.last_frame_time = time.perf_counter()
        self.frame_times_ms = []
        self.video_writer = None

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)

        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

        logging.info("Connecting to camera...")
        try:
            sock.connect((self.ip, self.port))
        except OSError:
            sock.close()
            raise
        logging.info("Connected to camera.")

        return sock

    def recv_lima_header(self, sock):
        header = bytearray()

        while True:
            b = sock.recv(1)

            if not b:
                raise ConnectionError("Socket closed while reading header.")

            header.extend(b)

            if b == b">":
                break

            if len(header) > 2048:
                raise ValueError(f"Invalid header: {header[:300]}")

        return bytes(header)

    def extract_datalen(self, header_bytes):
        header_str = header_bytes.decode(errors="ignore")
        match = re.search(r'DATALEN="(\d+)"', header_str)

        if not match:
            raise ValueError(f"DATALEN not found in header: {header_str}")

        return int(match.group(1))

    def recv_exactly(self, sock, n_bytes):
        data = bytearray(n_bytes)
        view = memoryview(data)
        received_total = 0

        while received_total < n_bytes:
            received = sock.recv_into(
                view[received_total:],
                min(RECV_CHUNK_SIZE, n_bytes - received_total)
            )

            if received == 0:
                raise ConnectionError("Socket closed while receiving image data.")

            received_total += received

        return data

    def decode_bmp(self, image_data):
        arr = np.frombuffer(image_data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if frame is None:
            pil_image = Image.open(io.BytesIO(image_data))
            frame = np.array(pil_image)

            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        return frame

    def take_frame(self, sock):
        sock.sendall(COMMAND.encode("ascii"))

        header = self.recv_lima_header(sock)
        data_length = self.extract_datalen(header)

        image_data = self.recv_exactly(sock, data_length)
        frame = self.decode_bmp(image_data)

        return frame, data_length

    def init_video_writer(self):
        if self.output_path.exists():
            raise FileExistsError(f"Output already exists: {self.output_path}")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        self.video_writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        if not self.video_writer.isOpened():
            raise RuntimeError("Could not open video writer.")

        logging.info(f"Saving video to: {self.output_path}")

    def run(self):
        sock = self.connect()
        try:
            cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Video Stream", WINDOW_WIDTH, WINDOW_HEIGHT)

            if self.save_video:
                self.init_video_writer()

            next_frame_time = time.perf_counter()

            while True:
                frame, data_length = self.take_frame(sock)

                now = time.perf_counter()
                frame_dt_ms = (now - self.last_frame_time) * 1000
                self.last_frame_time = now

                self.frame_times_ms.append(frame_dt_ms)
                if len(self.frame_times_ms) > 120:
                    self.frame_times_ms.pop(0)

                self.frame_count += 1

                relative_time = now - self.start_time
                avg_fps = self.frame_count / relative_time if relative_time > 0 else 0

                display = cv2.resize(
                    frame,
                    (WINDOW_WIDTH, WINDOW_HEIGHT),
                    interpolation=cv2.INTER_NEAREST
                )

                cv2.putText(
                    display,
                    f"Average FPS: {avg_fps:.2f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display,
                    f"Relative time: {relative_time:.2f} s",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )

                # Save frame to video
                if self.save_video and self.video_writer is not None:
                    self.video_writer.write(display)

                cv2.imshow("Video Stream", display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

                next_frame_time += self.frame_interval
                sleep_time = next_frame_time - time.perf_counter()

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_frame_time = time.perf_counter()

        finally:
            sock.close()

            if self.video_writer is not None:
                self.video_writer.release()
                logging.info(f"Video writer closed: {self.output_path}")

            cv2.destroyAllWindows()

            total_time = time.perf_counter() - self.start_time
            if total_time > 0:
                logging.info(f"Final average FPS: {self.frame_count / total_time:.2f}")


def positive_fps(value):
    """Validate a CLI frame rate, including NaN and infinity."""
    try:
        fps = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("FPS must be a number.") from error
    if not math.isfinite(fps) or fps <= 0:
        raise argparse.ArgumentTypeError("FPS must be finite and greater than zero.")
    return fps


def port_number(value):
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Port must be an integer.") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")
    return port


def build_parser():
    parser = argparse.ArgumentParser(description="Visualizar e gravar a smartcamera LIMA.")
    parser.add_argument("--ip", default=IP, help=f"IP ou hostname da camara (predefinido: {IP}).")
    parser.add_argument("--port", type=port_number, default=PORT, help=f"Porta TCP (predefinida: {PORT}).")
    parser.add_argument("--fps", type=positive_fps, default=TARGET_FPS, help="FPS alvo e FPS fixos do ficheiro (predefinido: 20).")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path, help="Ficheiro .mp4 novo; por omissao, gera um nome em data/videos/captures/.")
    output.add_argument("--no-save", action="store_true", help="Mostrar a captura sem gravar video.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        camera = SmartCameraStableFPS(
            ip=args.ip, port=args.port, fps=args.fps,
            output_path=args.output, save_video=not args.no_save,
        )
    except ValueError as error:
        parser.error(str(error))

    if camera.save_video and camera.output_path.exists():
        parser.error(f"Output already exists: {camera.output_path}")

    try:
        camera.run()
    except KeyboardInterrupt:
        logging.info("Capture interrupted.")
        return 130
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        logging.error("Capture failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
