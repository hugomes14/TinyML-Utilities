import cv2
from ultralytics import YOLO

class YOLOHandler:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.class_names = self.model.names if self.model.names else ['caixa-de-cima', 'caixa-de-lado', 'defeito']
    
    def detect_objects(self, video_path, output_path="output.mp4", **kwargs):
        conf_threshold = kwargs.get("conf_threshold", 0.5)
        show_video = kwargs.get("show_video", True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video file.")
            return
        
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        if show_video:
            cv2.namedWindow("YOLO Video Detection", cv2.WINDOW_NORMAL)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Warning: Failed to read frame. Exiting...")
                break
            
            try:
                results = self.model.predict(frame, conf=conf_threshold, verbose=False)
                result = results[0]
            except Exception as e:
                print(f"Error during YOLO inference: {e}")
                break
            
            if result.boxes:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for box, conf, cls in zip(boxes, confs, class_ids):
                    x1, y1, x2, y2 = map(int, box)
                    label = f"{self.class_names[cls]}: {conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            out.write(frame)
            if show_video:
                cv2.imshow("YOLO Video Detection", frame)
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break
            else:
                cv2.waitKey(10)  # Ensures OpenCV processes window events
        
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    def train_model(self, data_yaml, **kwargs):
        epochs = kwargs.get("epochs", 100)
        img_size = kwargs.get("img_size", 640)
        batch_size = kwargs.get("batch_size", 16)
        device = kwargs.get("device", "cpu")
        workers = kwargs.get("workers", 4)
        optimizer = kwargs.get("optimizer", "AdamW")
        lr0 = kwargs.get("lr0", 0.001)
        cos_lr = kwargs.get("cos_lr", True)
        augment = kwargs.get("augment", True)
        patience = kwargs.get("patience", 5)

        self.model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=device,
            workers=workers,
            optimizer=optimizer,
            lr0=lr0,
            cos_lr=cos_lr,
            augment=augment,
            patience=patience
        )
