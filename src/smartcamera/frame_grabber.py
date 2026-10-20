"""Video navigation with VFR timestamps and export of the visible native frame."""

import argparse
from pathlib import Path
import sys

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)

from .video import VideoReader


class VideoFrameGrabber(QWidget):
    def __init__(self, videos_dir="data/videos", frames_dir="data/frames"):
        super().__init__()
        self.videos_dir, self.frames_dir = Path(videos_dir), Path(frames_dir)
        self.reader = None
        self.video_path = None
        self.total_frames = 0
        self.current_frame = 0
        self.current_image = None
        self.setWindowTitle("Video Frame Grabber")
        self.resize(1000, 700)

        self.video_label = QLabel("Open a video to begin")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.show_frame)
        self.open_button = QPushButton("Open Video")
        self.prev_button = QPushButton("Previous Frame")
        self.next_button = QPushButton("Next Frame")
        self.capture_button = QPushButton("Take Frame")
        self._navigation = (self.prev_button, self.next_button, self.capture_button)
        for button in self._navigation:
            button.setEnabled(False)
        self.open_button.clicked.connect(self.open_video)
        self.prev_button.clicked.connect(self.previous_frame)
        self.next_button.clicked.connect(self.next_frame)
        self.capture_button.clicked.connect(self.capture_frame)
        self.info_label = QLabel("Frame: - / -")
        self.info_label.setAlignment(Qt.AlignCenter)

        buttons = QHBoxLayout()
        for button in (self.open_button, *self._navigation):
            buttons.addWidget(button)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.info_label)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", str(self.videos_dir),
            "Video Files (*.mkv *.mp4 *.avi *.mov *.wmv);;All Files (*)",
        )
        if not path:
            return
        candidate = None
        try:
            candidate = VideoReader(path)
            image = candidate.read(0)
        except Exception as error:
            if candidate is not None:
                candidate.close()
            QMessageBox.critical(self, "Error", f"Could not open video: {error}")
            return

        previous = self.reader
        self.reader, self.video_path = candidate, path
        self.total_frames = candidate.total_frames
        self.current_frame, self.current_image = 0, image
        self.slider.blockSignals(True)
        self.slider.setRange(0, self.total_frames - 1)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.slider.setEnabled(True)
        for button in self._navigation:
            button.setEnabled(True)
        if previous is not None:
            previous.close()
        self._update_display()

    def _reset_slider(self):
        self.slider.blockSignals(True)
        self.slider.setValue(self.current_frame)
        self.slider.blockSignals(False)

    def show_frame(self, number):
        if self.reader is None:
            return
        number = max(0, min(number, self.total_frames - 1))
        try:
            image = self.reader.read(number)
        except Exception as error:
            self._reset_slider()
            QMessageBox.warning(self, "Warning", f"Could not read frame: {error}")
            return
        self.current_frame, self.current_image = number, image
        self._reset_slider()
        self._update_display()

    def _update_display(self):
        if self.current_image is None:
            return
        image = self.current_image
        if image.ndim == 2:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, _ = rgb.shape
        qt_image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation,
        ))
        seconds = self.reader.relative_time(self.current_frame)
        self.info_label.setText(
            f"Frame: {self.current_frame + 1} / {self.total_frames}    Time: {seconds:.3f}s"
        )

    def previous_frame(self):
        self.show_frame(self.current_frame - 1)

    def next_frame(self):
        self.show_frame(self.current_frame + 1)

    @staticmethod
    def save_image_unicode_path(image, save_path):
        path = Path(save_path)
        if not path.suffix:
            path = path.with_suffix(".png")
        extension = path.suffix.lower()
        if extension not in (".png", ".jpg", ".jpeg"):
            return False, str(path), "Invalid file extension."
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            success, encoded = cv2.imencode(extension, image)
            if not success:
                return False, str(path), "Could not encode image."
            encoded.tofile(path)
            if path.is_file() and path.stat().st_size > 0:
                return True, str(path), None
            return False, str(path), "File was not created or is empty."
        except Exception as error:
            return False, str(path), str(error)

    def capture_frame(self):
        if self.current_image is None:
            QMessageBox.warning(self, "No Video", "Please open a video first.")
            return
        default_name = self.frames_dir / f"{Path(self.video_path).stem}_frame_{self.current_frame + 1}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Frame", str(default_name),
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)",
        )
        if not path:
            return
        success, final_path, error = self.save_image_unicode_path(self.current_image, path)
        if success:
            QMessageBox.information(self, "Saved", f"Frame saved successfully:\n{final_path}")
        else:
            QMessageBox.critical(self, "Error", f"Could not save frame:\n{final_path}\n{error}")

    def resizeEvent(self, event):
        self._update_display()
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.reader is not None:
            self.reader.close()
        event.accept()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Navegar em videos, incluindo VFR, e guardar frames.")
    parser.add_argument("--videos-dir", type=Path, default=Path("data/videos"))
    parser.add_argument("--frames-dir", type=Path, default=Path("data/frames"))
    args = parser.parse_args(argv)
    app = QApplication([sys.argv[0]])
    window = VideoFrameGrabber(args.videos_dir, args.frames_dir)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
