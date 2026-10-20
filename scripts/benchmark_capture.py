"""Measure the client and FFV1 writer using synthetic BMP, without camera or UI."""

import argparse
import cProfile
import csv
from dataclasses import replace
from datetime import datetime
import io
import json
from pathlib import Path
import platform
import pstats
import time

import av
import cv2
import numpy as np

from smartcamera.client import LimaClient
from smartcamera.recording import SessionRecorder
from smartcamera.video import VideoReader


class MemorySocket:
    def __init__(self, payload):
        self.payload = payload
        self.position = 0
        self.calls = 0

    def settimeout(self, seconds):
        pass

    def sendall(self, command):
        self.position = 0

    def recv(self, count):
        self.calls += 1
        result = self.payload[self.position:self.position + count]
        self.position += len(result)
        return result

    def recv_into(self, buffer, count):
        data = self.recv(count)
        buffer[:len(data)] = data
        return len(data)


def distribution(values):
    return {"median_ms": float(np.median(values)), "p95_ms": float(np.percentile(values, 95))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=100)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be positive")
    folder = Path("data/benchmarks") / f"run_{datetime.now():%Y%m%d_%H%M%S_%f}"
    folder.mkdir(parents=True)
    image = np.random.default_rng(42).integers(0, 256, (480, 640), dtype=np.uint8)
    success, encoded = cv2.imencode(".bmp", image)
    if not success:
        raise RuntimeError("BMP encoding failed")
    payload = f'<LIMA DATALEN="{encoded.nbytes}"/>'.encode() + encoded.tobytes()
    sock = MemorySocket(payload)
    client = LimaClient("simulated", 33040)
    client.sock = sock
    for _ in range(10):
        client.take_frame()
    calls_before = sock.calls
    elapsed = []
    profile = cProfile.Profile()
    profile.enable()
    for _ in range(args.frames):
        started = time.perf_counter_ns()
        client.take_frame()
        elapsed.append((time.perf_counter_ns() - started) / 1e6)
    profile.disable()
    receive_calls = (sock.calls - calls_before) / args.frames
    profile_text = io.StringIO()
    pstats.Stats(profile, stream=profile_text).sort_stats("cumulative").print_stats(15)
    (folder / "client-profile.txt").write_text(profile_text.getvalue(), encoding="utf-8")

    recorder = SessionRecorder(folder / "synthetic.mkv", {"target_fps": 20, "synthetic_timestamps": True})
    try:
        for index in range(args.frames):
            actual = client.take_frame()
            received = 1_000_000_000 + index * 50_000_000
            simulated = replace(
                actual, received_ns=received,
                requested_ns=received - (actual.received_ns - actual.requested_ns),
                decoded_ns=received + (actual.decoded_ns - actual.received_ns),
            )
            recorder.write(simulated)
    finally:
        recorder.close(1_000_000_000 + args.frames * 50_000_000)
    with (folder / "synthetic.frames.csv").open(encoding="utf-8", newline="") as handle:
        record_times = [float(row["record_ms"]) for row in csv.DictReader(handle)]
    index_times = []
    for _ in range(3):
        started = time.perf_counter_ns()
        reader = VideoReader(folder / "synthetic.mkv")
        reader.close()
        index_times.append((time.perf_counter_ns() - started) / 1e6)
    report = {
        "case": "640x480 random uint8 BMP, in-memory socket, no network or UI",
        "frames": args.frames, "client_with_cprofile": distribution(elapsed),
        "recv_calls_per_frame": receive_calls,
        "ffv1_record_no_profiler": distribution(record_times),
        "ffv1_index": distribution(index_times),
        "video_bytes": (folder / "synthetic.mkv").stat().st_size,
        "versions": {"python": platform.python_version(), "av": av.__version__, "opencv": cv2.__version__, "numpy": np.__version__},
    }
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Artifacts: {folder}")


if __name__ == "__main__":
    main()
