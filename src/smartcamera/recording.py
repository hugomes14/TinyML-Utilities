"""Lossless VFR recording and incremental session metadata."""

import csv
from fractions import Fraction
import json
from pathlib import Path
import time

import av
import numpy as np


TIME_BASE = Fraction(1, 1000)
NS_PER_TICK = 1_000_000
CSV_FIELDS = (
    "frame_index", "request_started_ns", "received_ns", "received_utc",
    "elapsed_ns", "video_pts_ms", "response_bytes", "request_receive_ms",
    "decode_ms", "record_ms",
)


def output_paths(path):
    path = Path(path)
    return path, path.with_suffix(".frames.csv"), path.with_suffix(".session.json")


class StageStats:
    def __init__(self):
        self.count = 0
        self.total_ms = 0.0
        self.max_ms = 0.0

    def add(self, milliseconds):
        self.count += 1
        self.total_ms += milliseconds
        self.max_ms = max(self.max_ms, milliseconds)

    def summary(self):
        return {
            "count": self.count,
            "mean_ms": self.total_ms / self.count if self.count else None,
            "max_ms": self.max_ms if self.count else None,
        }


class SessionRecorder:
    """Hold one encoded packet until its actual display duration is known."""

    def __init__(self, path, configuration):
        self.path, csv_path, json_path = output_paths(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._files = []
        created = []
        try:
            for target, mode in ((self.path, "xb"), (csv_path, "x"), (json_path, "x")):
                options = {} if "b" in mode else {"encoding": "utf-8", "newline": ""}
                handle = target.open(mode, **options)
                created.append(target)
                self._files.append(handle)
        except BaseException:
            for handle in self._files:
                handle.close()
            for target in created:
                target.unlink()
            raise
        self._video_file, self._csv_file, self._json_file = self._files
        self.container = None
        self.stream = None
        self._pending = []
        self._last_pts = None
        self.origin_ns = None
        self.frame_count = 0
        self.closed = False
        self.stages = {name: StageStats() for name in ("request_receive", "decode", "record", "preview")}
        self.summary = {
            "schema_version": 1, "status": "recording", "configuration": configuration,
            "codec": "ffv1", "container": "matroska", "time_base": "1/1000",
            "timestamp_source": "host_complete_response", "frame_count": 0,
        }
        try:
            self._csv = csv.DictWriter(self._csv_file, fieldnames=CSV_FIELDS)
            self._csv.writeheader()
            self._csv_file.flush()
            self._save_summary()
            self.container = av.open(self._video_file, "w", format="matroska")
        except BaseException as error:
            self.summary.update(status="error", stop_reason=f"Initialization failed: {error}")
            try:
                self._save_summary()
            finally:
                for handle in self._files:
                    handle.close()
            raise

    def _save_summary(self):
        self._json_file.seek(0)
        json.dump(self.summary, self._json_file, ensure_ascii=False, indent=2)
        self._json_file.truncate()
        self._json_file.flush()

    def _init_stream(self, image):
        height, width = image.shape[:2]
        self._shape = image.shape
        if image.dtype != np.uint8:
            raise ValueError("FFV1 recording expects uint8 pixels.")
        if image.ndim == 2:
            self._array_format, pixel_format = "gray", "gray"
        elif image.ndim == 3 and image.shape[2] == 3:
            self._array_format, pixel_format = "bgr24", "bgr0"
        elif image.ndim == 3 and image.shape[2] == 4:
            self._array_format, pixel_format = "bgra", "bgra"
        else:
            raise ValueError("Unsupported frame layout.")
        self.stream = self.container.add_stream("ffv1", rate=None)
        self.stream.width, self.stream.height = width, height
        self.stream.pix_fmt = pixel_format
        self.stream.time_base = TIME_BASE
        self.stream.codec_context.time_base = TIME_BASE
        self.summary.update(width=width, height=height, pixel_format=pixel_format)

    def _mux_pending(self, end_pts):
        for packet in self._pending:
            packet.duration = max(1, end_pts - self._last_pts)
            self.container.mux(packet)
        self._pending.clear()

    def write(self, sample):
        started = time.perf_counter_ns()
        if self.closed:
            raise RuntimeError("Recording has already closed.")
        if self.stream is None:
            self._init_stream(sample.image)
            self.origin_ns = sample.received_ns
            self.summary.update(first_received_ns=self.origin_ns, first_received_utc=sample.received_utc)
        if sample.image.shape != self._shape or sample.image.dtype != np.uint8:
            raise ValueError("Camera changed pixel layout or resolution during recording.")
        elapsed = sample.received_ns - self.origin_ns
        pts = round(elapsed / NS_PER_TICK)
        if self._last_pts is not None and pts <= self._last_pts:
            raise ValueError("Frame timestamps must increase at millisecond resolution.")
        frame = av.VideoFrame.from_ndarray(sample.image, format=self._array_format)
        frame.pts, frame.time_base = pts, TIME_BASE
        packets = self.stream.encode(frame)
        # Keep the preceding packet pending if encoding this image fails, so
        # controlled shutdown can still give the last good image its duration.
        self._mux_pending(pts)
        self._pending = packets
        self._last_pts = pts
        self.frame_count += 1
        record_ms = (time.perf_counter_ns() - started) / 1e6
        request_ms = (sample.received_ns - sample.requested_ns) / 1e6
        decode_ms = (sample.decoded_ns - sample.received_ns) / 1e6
        for name, value in (("request_receive", request_ms), ("decode", decode_ms), ("record", record_ms)):
            self.stages[name].add(value)
        self._csv.writerow(dict(zip(CSV_FIELDS, (
            self.frame_count, sample.requested_ns, sample.received_ns, sample.received_utc,
            elapsed, pts, sample.data_length, request_ms, decode_ms, record_ms,
        ))))
        self._csv_file.flush()

    def close(self, ended_ns, status="completed", reason="user_stop"):
        if self.closed:
            return
        self.closed = True
        finalization_error = None
        try:
            if self.stream is not None:
                end_pts = max(self._last_pts + 1, round((ended_ns - self.origin_ns) / NS_PER_TICK))
                self._mux_pending(end_pts)
                for packet in self.stream.encode():
                    self.container.mux(packet)
                self.summary["video_duration_ms"] = end_pts
        except Exception as error:
            finalization_error = error
            status, reason = "error", f"Finalization failed: {error}; previous reason: {reason}"
        finally:
            try:
                if self.container is not None:
                    self.container.close()
            except Exception as error:
                finalization_error = error
                status, reason = "error", f"Container close failed: {error}; previous reason: {reason}"
            self.summary.update(
                status=status, stop_reason=reason, ended_ns=ended_ns,
                frame_count=self.frame_count,
                elapsed_ns=ended_ns - self.origin_ns if self.origin_ns is not None else None,
                stages={name: stage.summary() for name, stage in self.stages.items()},
            )
            try:
                self._save_summary()
            finally:
                for handle in self._files:
                    handle.close()
        if finalization_error is not None:
            raise finalization_error
