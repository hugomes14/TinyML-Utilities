# TinyML-Utilities

A collection of Python utilities for TinyML projects focused on object detection with YOLO, video annotation, and Arduino-based camera hardware.

## Project Structure

```
TinyML-Utilities/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── yolo.py                   # YOLO object detection & training
│   ├── video_utils.py            # Video playback & dataset annotation tools
│   ├── arduino.py                # Arduino CLI integration & sketch management
│   ├── b6_smart_camera.py        # IP Smart Camera TCP communication
│   └── CameraCaptureRawBytes1/   # Arduino firmware
│       └── CameraCaptureRawBytes1.ino
├── tests/                        # Test scripts & standalone tools
│   ├── test1_yolo_crop.py        # YOLO dataset annotation example
│   ├── video_frame_grabber.py    # PyQt5 video frame grabber GUI
│   ├── teste1.py                 # Video playback example
│   ├── teste2.py                 # Arduino compile/upload example
│   ├── teste3.py                 # Serial video capture example
│   ├── teste4.py                 # Additional tests
│   ├── teste5.py                 # Additional tests
│   └── datasets/                 # Dataset directories
│       ├── caixa2.v1i.yolov8/    # Roboflow-format dataset
│       ├── dataset.yolov11/      # YOLOv11-format dataset
│       └── yolo_dataset/         # YOLO-format dataset (images/labels/)
├── models_yolo/                  # Pre-trained YOLO models
│   ├── yolov8n.pt, yolov8s.pt    # YOLOv8 nano/small
│   ├── yolov8l.pt, yolov8x.pt    # YOLOv8 large/xlarge
│   ├── yolov4.weights, yolov4.cfg
│   └── coco.names
├── runs/detect/                  # YOLO training outputs (22 runs)
│   └── train*/                   # Per-run weights, args.yaml, results
├── videos/                       # Test videos
├── positive_dataset/             # Collected positive samples
├── negative_dataset/             # Collected negative samples
├── setup.py                      # Package setup
└── requirements.txt              # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- [Arduino CLI](https://arduino.github.io/arduino-cli/latest/getting-started/) (for firmware upload)
- Virtual environment (recommended)

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Install package in development mode (optional)
pip install -e .
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `ultralytics` | YOLOv8/v11 object detection & training |
| `opencv-python` (cv2) | Video capture, image processing |
| `matplotlib` | Video visualization, interactive annotation |
| `numpy` | Array operations |
| `Pillow` | Image decoding (BMP, etc.) |
| `pyserial` | Serial communication with Arduino |
| `PyQt5` | GUI for video frame grabber |

## Modules

### 1. YOLO Object Detection (`src/yolo.py`)

`YOLOHandler` class for running inference and training YOLO models.

```python
from src.yolo import YOLOHandler

# Load a pre-trained model
handler = YOLOHandler("models_yolo/yolov8n.pt")

# Run detection on a video
handler.detect_objects(
    video_path="videos/test.mp4",
    output_path="output.mp4",
    conf_threshold=0.5,
    show_video=True
)

# Train a new model
handler.train_model(
    data_yaml="datasets/dataset.yolov11/data.yaml",
    epochs=100,
    img_size=640,
    batch_size=16,
    device="cpu"  # or "0" for GPU
)
```

**Class: `YOLOHandler`**

| Method | Description |
|--------|-------------|
| `__init__(model_path)` | Load YOLO model from file |
| `detect_objects(video_path, **kwargs)` | Run inference on video, save annotated output |
| `train_model(data_yaml, **kwargs)` | Train a new YOLO model |

**`detect_objects` parameters:**
- `video_path` — Path to input video
- `output_path` — Path for annotated output video (default: `output.mp4`)
- `conf_threshold` — Confidence threshold (default: `0.5`)
- `show_video` — Display detection in real-time (default: `True`)

**`train_model` parameters:**
- `data_yaml` — Path to dataset YAML file
- `epochs` — Training epochs (default: `100`)
- `img_size` — Input image size (default: `640`)
- `batch_size` — Batch size (default: `16`)
- `device` — Device: `"cpu"`, `"0"`, etc. (default: `"cpu"`)
- `workers` — DataLoader workers (default: `4`)
- `optimizer` — Optimizer: `"AdamW"` (default), `"SGD"`
- `lr0` — Initial learning rate (default: `0.001`)
- `patience` — Early stopping patience (default: `5`)

### 2. Video Utilities (`src/video_utils.py`)

Three classes for video handling and dataset annotation:

#### `VideoRunner` — Basic Video Player

```python
from src.video_utils import VideoRunner

video = VideoRunner("test.mp4", "videos/")
video.play_it(speed=0.001)
```

#### `VideoCrop` — Positive/Negative Dataset Collection

Interactive tool for cropping positive and negative samples from video:

```python
from src.video_utils import VideoCrop

video = VideoCrop(
    video_name="test.mp4",
    dir="videos/",
    negative_dataset="negative_dataset/",
    positive_dataset="positive_dataset/"
)
video.dataset_constructer()
```

**Controls:**
- **Positive Dataset** — Save current crop to positive dataset
- **Negative Dataset** — Save current crop to negative dataset
- **Next Frame** — Advance to next frame
- **Mouse** — Click & drag to draw rectangle, release to crop

#### `VideoCropYolo` — YOLO Dataset Annotation

Interactive tool for annotating objects in YOLO format:

```python
from src.video_utils import VideoCropYolo

video = VideoCropYolo(
    video_name="test.mp4",
    dir="tests/",
    dataset="yolo_dataset",
    file_number=2  # Starting image index
)
video.dataset_constructer()
```

**Controls:**
- **Frente de onda** (label `0`) — Save crop with class "frente de onda"
- **Fonte** (label `1`) — Save crop with class "fonte"
- **Next Frame** — Advance to next frame
- **Mouse** — Click & drag to draw rectangle, release to save

**Label format:** `YOLO text format` — normalized center coordinates + width/height relative to frame size.

### 3. Arduino Integration (`src/arduino.py`)

`SketchConfig` class for compiling and uploading Arduino firmware:

```python
from src.arduino import SketchConfig

config = SketchConfig(
    arduino_cli_path="arduino-cli",
    board="arduino:mbed_nano:nano33ble",
    port="COM3",
    sketch_path="src\\CameraCaptureRawBytes1\\CameraCaptureRawBytes1.ino",
    frames_width=320,
    frames_height=240,
    baud_rate=256000
)

# Compile only
config.compile()

# Upload to board
config.upload()
```

### 4. Smart Camera (`src/b6_smart_camera.py`)

`SmartCameraStableFPS` class for connecting to a Lima Smart Camera via TCP:

```python
from src.b6_smart_camera import SmartCameraStableFPS

camera = SmartCameraStableFPS()
sock = camera.connect()
# Receive frames using camera.recv_lima_header(), camera.recv_exactly(), camera.decode_bmp()
```

**Configuration:**
- IP: `192.168.249.197`
- Port: `33040`
- Protocol: LIMA (`<LIMA DIR="Request" CMD="Project_GetImage" .../>`)
- Output: BMP decoding, stable FPS video recording

## Hardware Configuration

### Arduino Nano 33 BLE + OV767X Camera

| Parameter | Value |
|-----------|-------|
| Board | `arduino:mbed_nano:nano33ble` |
| Camera | OV767X (QVGA 320x240, grayscale) |
| Baud Rate | 256000 |
| Frame Size | 320 × 240 = 76,800 bytes |
| Sync Byte | `0xC0` (start/end of frame) |

The Arduino sketch (`CameraCaptureRawBytes1.ino`) waits for a `0xC0` byte on Serial to trigger each frame capture, then sends the raw grayscale data followed by another `0xC0` sync byte.

## Dataset Workflow

### 1. Collect Data

Use `VideoCropYolo` to annotate frames:

```bash
python tests/test1_yolo_crop.py
```

This launches an interactive window where you:
1. Navigate frames with **Next Frame**
2. Draw rectangles around objects
3. Click **Frente de onda** or **Fonte** to save with the correct label

### 2. Dataset Structure

YOLO format requires:
```
yolo_dataset/
├── images/
│   ├── 1.jpeg, 2.jpeg, ...
└── labels/
    ├── 1.txt, 2.txt, ...
```

Each label file contains one line per object:
```
<class_id> <x_center> <y_center> <width> <height>
```
All values normalized to [0, 1].

### 3. Create data.yaml

```yaml
path: ./datasets/yolo_dataset
train: images/train
val: images/valid
test: images/test

nc: 2
names: ["frente de onda", "fonte"]
```

### 4. Train Model

```python
from src.yolo import YOLOHandler

handler = YOLOHandler("models_yolo/yolov8n.pt")
handler.train_model(
    data_yaml="datasets/yolo_dataset/data.yaml",
    epochs=100,
    img_size=640,
    batch_size=16
)
```

Training outputs are saved in `runs/detect/train*/`.

## Training Outputs

Results from previous training runs are stored in `runs/detect/`:

| Run | Has Best Weights | Has Results |
|-----|-------------------|-------------|
| train7 | Yes | Yes |
| train8 | Yes | Yes |
| train13 | Yes | Yes |
| train15 | Yes | Yes |
| Others | No | No |

Best models: `runs/detect/train{N}/weights/best.pt`

## Video Frame Grabber (`tests/video_frame_grabber.py`)

Standalone PyQt5 GUI for navigating videos and capturing individual frames:

```python
python tests/video_frame_grabber.py
```

**Features:**
- Open any video file
- Navigate frames with slider or prev/next buttons
- Capture individual frames to disk

## Cleanup Recommendations

The workspace has accumulated significant artifacts. Consider:

1. **Move videos** from root to `videos/` directory
2. **Clean old training runs** in `runs/detect/` (keep only best models)
3. **Fix `requirements.txt`** — current file appears corrupted (UTF-16 binary content)
4. **Add `docs/` content** — currently an empty `__init__.py`
5. **Consolidate `positive_dataset/` and `negative_dataset/`** into `datasets/`
6. **Remove `venv/` from repository** — ensure it's in `.gitignore`

## Author

Hugo Gomes — hugo.gomes1415@gmail.com

## License

See [LICENSE](LICENSE) file.
