from ultralytics import YOLO

# Load a YOLOv8 model (pretrained or custom)
model = YOLO("yolov8n.pt")  # 'n' stands for nano, you can use 's', 'm', 'l', 'x'

# Train the model on your dataset
model.train(
    data="./dataset.yolov11/data.yaml",  # Path to dataset config
    epochs=50,                     # Number of training epochs
    imgsz=640,                      # Image size
    batch=16,                       # Batch size
    device="cpu"                   # Use GPU (set "cpu" if no GPU)
)