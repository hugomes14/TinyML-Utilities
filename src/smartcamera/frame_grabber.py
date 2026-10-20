"""Interactive video navigation and frame export using PyQt5."""

import argparse
from pathlib import Path
import sys
import os
import cv2

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap


class VideoFrameGrabber(QWidget):
    def __init__(self, videos_dir="data/videos", frames_dir="data/frames"):
        super().__init__()

        self.videos_dir = Path(videos_dir)
        self.frames_dir = Path(frames_dir)

        self.setWindowTitle("Video Frame Grabber")
        self.resize(1000, 700)

        self.cap = None
        self.video_path = None
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 0
        self.current_image = None

        self.video_label = QLabel("Open a video to begin")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet("background-color: black; color: white;")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.slider_moved)

        self.open_button = QPushButton("Open Video")
        self.prev_button = QPushButton("← Previous Frame")
        self.next_button = QPushButton("Next Frame →")
        self.capture_button = QPushButton("Take Frame")

        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.capture_button.setEnabled(False)

        self.open_button.clicked.connect(self.open_video)
        self.prev_button.clicked.connect(self.previous_frame)
        self.next_button.clicked.connect(self.next_frame)
        self.capture_button.clicked.connect(self.capture_frame)

        self.info_label = QLabel("Frame: - / -")
        self.info_label.setAlignment(Qt.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.capture_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.info_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            str(self.videos_dir),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)",
        )

        if not file_path:
            return

        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            QMessageBox.critical(self, "Error", "Could not open video.")
            return

        if self.cap is not None:
            self.cap.release()

        self.cap = cap
        self.video_path = file_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0

        if self.total_frames <= 0:
            QMessageBox.critical(self, "Error", "This video has no readable frames.")
            return

        self.slider.setEnabled(True)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.total_frames - 1)
        self.slider.setValue(0)

        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.capture_button.setEnabled(True)

        self.show_frame(0)

    def show_frame(self, frame_number):
        if self.cap is None:
            return

        frame_number = max(0, min(frame_number, self.total_frames - 1))
        self.current_frame = frame_number

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = self.cap.read()

        if not success or frame is None:
            QMessageBox.warning(self, "Warning", "Could not read frame.")
            return

        self.current_image = frame.copy()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w

        qt_image = QImage(
            frame_rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(qt_image)

        scaled_pixmap = pixmap.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.video_label.setPixmap(scaled_pixmap)

        self.slider.blockSignals(True)
        self.slider.setValue(frame_number)
        self.slider.blockSignals(False)

        timestamp = frame_number / self.fps if self.fps else 0

        self.info_label.setText(
            f"Frame: {frame_number + 1} / {self.total_frames}    "
            f"Time: {timestamp:.2f}s"
        )

    def slider_moved(self, value):
        self.show_frame(value)

    def previous_frame(self):
        if self.cap is None:
            return

        self.show_frame(self.current_frame - 1)

    def next_frame(self):
        if self.cap is None:
            return

        self.show_frame(self.current_frame + 1)

    def save_image_unicode_path(self, image, save_path):
        """
        Saves images correctly on Windows, even when the path contains accents
        or special characters.
        """
        root, ext = os.path.splitext(save_path)

        if ext == "":
            ext = ".png"
            save_path = save_path + ext

        ext = ext.lower()

        if ext not in [".png", ".jpg", ".jpeg"]:
            return False, save_path, "Invalid file extension."

        folder = os.path.dirname(save_path)

        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        try:
            success, encoded_image = cv2.imencode(ext, image)

            if not success:
                return False, save_path, "Could not encode image."

            encoded_image.tofile(save_path)

            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                return True, save_path, None

            return False, save_path, "File was not created or is empty."

        except Exception as e:
            return False, save_path, str(e)

    def capture_frame(self):
        if self.cap is None:
            QMessageBox.warning(self, "No Video", "Please open a video first.")
            return

        default_name = str(
            self.frames_dir / f"{Path(self.video_path).stem}_frame_{self.current_frame + 1}.png"
        )

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Frame",
            default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*)",
        )

        if not save_path:
            return

        root, ext = os.path.splitext(save_path)

        if ext == "":
            save_path += ".png"
        elif ext.lower() not in [".png", ".jpg", ".jpeg"]:
            QMessageBox.warning(
                self,
                "Invalid File Type",
                "Please save the frame as .png, .jpg, or .jpeg.",
            )
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        success, frame = self.cap.read()

        if not success or frame is None:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not read frame {self.current_frame + 1} from the video.",
            )
            return

        save_success, final_path, error_message = self.save_image_unicode_path(
            frame,
            save_path,
        )

        if save_success:
            QMessageBox.information(
                self,
                "Saved",
                f"Frame saved successfully:\n{final_path}",
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                (
                    "Could not save frame.\n\n"
                    f"Path tried:\n{final_path}\n\n"
                    f"Reason:\n{error_message}"
                ),
            )

    def resizeEvent(self, event):
        if self.cap is not None and self.current_image is not None:
            self.show_frame(self.current_frame)

        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()

        event.accept()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Navegar em videos e guardar frames.")
    parser.add_argument("--videos-dir", type=Path, default=Path("data/videos"), help="Pasta inicial dos videos (predefinida: data/videos).")
    parser.add_argument("--frames-dir", type=Path, default=Path("data/frames"), help="Pasta sugerida para guardar frames (predefinida: data/frames).")
    args = parser.parse_args(argv)
    app = QApplication([sys.argv[0]])
    window = VideoFrameGrabber(videos_dir=args.videos_dir, frames_dir=args.frames_dir)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
