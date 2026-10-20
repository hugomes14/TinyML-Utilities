"""Manual LIMA capture with native lossless video and host timestamps."""

import argparse
from datetime import datetime
import logging
import math
from pathlib import Path
import time

import av
import cv2

from .client import COMMAND, LimaClient
from .recording import SessionRecorder, output_paths


IP = "192.168.249.197"
PORT = 33040
TARGET_FPS = 20
WINDOW_WIDTH, WINDOW_HEIGHT = 960, 720
DEFAULT_OUTPUT_DIR = Path("data/videos/captures")


class SmartCameraCapture:
    """Acquire each frame once; target FPS limits requests, never video time."""

    def __init__(self, ip=IP, port=PORT, fps=TARGET_FPS, output_path=None,
                 save_video=True, timeout=5.0):
        if not ip.strip():
            raise ValueError("Camera IP or hostname must not be empty.")
        if not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("Port must be an integer between 1 and 65535.")
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("FPS must be finite and greater than zero.")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be finite and greater than zero.")
        self.ip, self.port, self.fps, self.timeout = ip, port, fps, timeout
        self.frame_interval = 1.0 / fps
        self.save_video = save_video
        self.output_path = Path(output_path) if output_path is not None else (
            DEFAULT_OUTPUT_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S_%f}.mkv"
        )
        if save_video and self.output_path.suffix.lower() != ".mkv":
            raise ValueError("Lossless capture output must have an .mkv extension.")
        self.frame_count = 0

    def _preview(self, sample, elapsed_ns):
        image = sample.image
        if image.ndim == 2:
            display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            display = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            display = image
        # Always allocate the preview so overlays cannot alter the recorded pixels.
        display = cv2.resize(display, (WINDOW_WIDTH, WINDOW_HEIGHT), interpolation=cv2.INTER_NEAREST)
        elapsed = elapsed_ns / 1e9
        fps = (self.frame_count - 1) / elapsed if elapsed > 0 else 0.0
        for text, y in ((f"Received FPS: {fps:.2f}", 40), (f"Relative time: {elapsed:.3f} s", 80)):
            cv2.putText(display, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.imshow("Video Stream", display)
        return cv2.waitKey(1) & 0xFF

    def run(self):
        client = LimaClient(self.ip, self.port, self.timeout)
        recorder = None
        window_open = False
        status, reason = "completed", "user_stop"
        self.frame_count = 0
        origin_ns = None
        try:
            if self.save_video:
                recorder = SessionRecorder(self.output_path, {
                    "ip": self.ip, "port": self.port,
                    "target_fps": self.fps, "frame_timeout_s": self.timeout,
                    "command": COMMAND,
                })
            logging.info("Connecting to %s:%s", self.ip, self.port)
            client.connect()
            cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)
            window_open = True
            cv2.resizeWindow("Video Stream", WINDOW_WIDTH, WINDOW_HEIGHT)
            next_request_ns = time.perf_counter_ns()
            while True:
                sample = client.take_frame()
                if origin_ns is None:
                    origin_ns = sample.received_ns
                self.frame_count += 1
                if recorder is not None:
                    recorder.write(sample)
                started = time.perf_counter_ns()
                key = self._preview(sample, sample.received_ns - origin_ns)
                if recorder is not None:
                    recorder.stages["preview"].add((time.perf_counter_ns() - started) / 1e6)
                if key == ord("q"):
                    break
                next_request_ns += round(self.frame_interval * 1e9)
                now = time.perf_counter_ns()
                if next_request_ns > now:
                    time.sleep((next_request_ns - now) / 1e9)
                else:
                    next_request_ns = now
        except KeyboardInterrupt:
            status, reason = "interrupted", "keyboard_interrupt"
            raise
        except Exception as error:
            status, reason = "error", f"{type(error).__name__}: {error}"
            raise
        finally:
            ended_ns = time.perf_counter_ns()
            try:
                client.close()
            finally:
                try:
                    if recorder is not None:
                        recorder.close(ended_ns, status, reason)
                        logging.info("Recording closed: %s (%s, %d frames)",
                                     self.output_path, status, recorder.frame_count)
                finally:
                    if window_open:
                        cv2.destroyAllWindows()


# Keep the previously documented Python import available.
SmartCameraStableFPS = SmartCameraCapture


def positive_number(value):
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected a number.") from error
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Value must be finite and greater than zero.")
    return number


def port_number(value):
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Port must be an integer.") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")
    return port


def build_parser():
    parser = argparse.ArgumentParser(description="Captura LIMA sem perdas, com timestamps reais de rececao.")
    parser.add_argument("--ip", default=IP, help=f"IP ou hostname (predefinido: {IP}).")
    parser.add_argument("--port", type=port_number, default=PORT, help=f"Porta TCP (predefinida: {PORT}).")
    parser.add_argument("--fps", type=positive_number, default=TARGET_FPS,
                        help="Limite alvo de pedidos por segundo; nao define a duracao do video (20).")
    parser.add_argument("--timeout", type=positive_number, default=5.0,
                        help="Prazo total por resposta, em segundos (5).")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path,
                        help="Novo ficheiro .mkv; gera tambem .frames.csv e .session.json.")
    output.add_argument("--no-save", action="store_true", help="Apenas visualizar, sem video nem metadados.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        camera = SmartCameraCapture(
            ip=args.ip, port=args.port, fps=args.fps, output_path=args.output,
            save_video=not args.no_save, timeout=args.timeout,
        )
    except ValueError as error:
        parser.error(str(error))
    if camera.save_video:
        for path in output_paths(camera.output_path):
            if path.exists():
                parser.error(f"Output already exists: {path}")
    try:
        camera.run()
    except KeyboardInterrupt:
        logging.info("Capture interrupted.")
        return 130
    except (OSError, ValueError, RuntimeError, cv2.error, av.error.FFmpegError) as error:
        logging.error("Capture failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
