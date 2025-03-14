from src.yolo import YOLOHandler

# Initialize YOLO handler with trained model
yolo = YOLOHandler("yolo11l.pt") #yolov8s.pt ....

# Run object detection with custom parameters
"""yolo.detect_objects(
    video_path="./tests/videos/caixa.avi",
    output_path="output.mp4",
    conf_threshold=0.4,  # Set custom confidence threshold
    show_video=True  # Disable video display
)"""

# Train a new model with custom parameters
yolo.train_model(
    data_yaml="./tests/datasets/caixa2.yolov8/data.yaml",
    epochs=200,
    img_size=640,
    batch_size=10,
    device="cuda",
    workers = 4,
    optimizer="SGD",
    lr0=0.01,
    cos_lr= True,
    augment= True,
    patience=100,
    project="custom_logs"
)


