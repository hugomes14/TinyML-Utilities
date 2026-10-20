from src.yolo import YOLOHandler

# Initialize YOLO handler with trained model
yolo = YOLOHandler("./runs/detect/train15/weights/best.pt") #yolov8s.pt ....

# Run object detection with custom parameters
yolo.detect_objects(
    video_path="./tests/videos/caixa.avi",
    output_path="output.mp4",
    conf_threshold=0.4,  # Set custom confidence threshold
    show_video=True  # Disable video display
)

# Train a new model with custom parameters
"""yolo.train_model(
    data_yaml="./tests/datasets/caixa2.v1i.yolov8/data.yaml",
    epochs=50,
    batch_size=8,
    device="cpu"  # Use GPU if available
)"""
