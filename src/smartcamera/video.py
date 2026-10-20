"""Frame indexing with actual presentation timestamps, including VFR video."""

from pathlib import Path

import av


def native_array(frame):
    if frame.format.name == "gray":
        return frame.to_ndarray(format="gray")
    if frame.format.name == "bgra":
        return frame.to_ndarray(format="bgra")
    return frame.to_ndarray(format="bgr24")


class VideoReader:
    """Index timestamps once and retain only the currently selected image."""

    def __init__(self, path):
        self.path = Path(path)
        self.container = av.open(str(self.path))
        self.closed = False
        self.index = None
        self._image = None
        self.timestamps = []
        self._pts = []
        try:
            if not self.container.streams.video:
                raise ValueError("This file has no video stream.")
            self.stream = self.container.streams.video[0]
            # FFV1 has one independently decodable frame per packet. Index its
            # timestamps without decoding every image just to count frames.
            is_ffv1 = self.stream.codec_context.name == "ffv1"
            source = self.container.demux(self.stream) if is_ffv1 else self.container.decode(self.stream)
            for item in source:
                if is_ffv1 and item.size == 0:
                    continue
                if item.pts is None:
                    raise ValueError("Video frame has no presentation timestamp.")
                pts = round(item.pts * item.time_base / self.stream.time_base)
                if self._pts and pts <= self._pts[-1]:
                    raise ValueError("Video timestamps do not increase.")
                self._pts.append(pts)
                self.timestamps.append(float(item.pts * item.time_base))
                if not is_ffv1 and self._image is None:
                    self._image = native_array(item)
            if not self._pts:
                raise ValueError("This video has no readable frames.")
            self.total_frames = len(self._pts)
            if is_ffv1:
                self.read(0)
            else:
                self.index = 0
        except BaseException:
            self.close()
            raise

    def read(self, index):
        if self.closed:
            raise RuntimeError("Video is closed.")
        if not 0 <= index < self.total_frames:
            raise IndexError("Frame index outside video.")
        if index == self.index:
            return self._image
        target = self._pts[index]
        self.container.seek(target, stream=self.stream, backward=True)
        for frame in self.container.decode(self.stream):
            pts = round(frame.pts * frame.time_base / self.stream.time_base)
            if pts == target:
                image = native_array(frame)
                self.index, self._image = index, image
                return image
            if pts > target:
                break
        raise ValueError("Could not decode the selected frame.")

    def relative_time(self, index):
        return self.timestamps[index] - self.timestamps[0]

    def close(self):
        if not self.closed:
            self.container.close()
            self.closed = True
