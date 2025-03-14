<<<<<<< HEAD
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
=======
import socket
import io
import threading
from PIL import Image
import numpy as np
import cv2
import datetime
import logging
import time
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Desired window dimensions (width, height)
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
COMMAND = '<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>'
IP = "192.168.100.1"
PORT = 33040

# YOLO paths
YOLO_WEIGHTS = "yolov3.weights"
YOLO_CONFIG = "yolov3.cfg"
YOLO_CLASSES = "coco.names"

# Load YOLO model and classes
net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
with open(YOLO_CLASSES, 'r') as f:
    classes = f.read().strip().split('\n')

# Define colors for bounding boxes
COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

def detect_objects(frame, net, classes, confidence_threshold=0.5, nms_threshold=0.4):
    height, width = frame.shape[:2]

    # Create a blob from the frame
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Get detection results
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]  # Fixed indexing
    detections = net.forward(output_layers)

    # Process detections
    boxes = []
    confidences = []
    class_ids = []

    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > confidence_threshold:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply Non-Max Suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

    # Draw bounding boxes and labels
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            confidence = confidences[i]
            color = COLORS[class_ids[i]]

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame

class SmartCamera:
    def __init__(self, ip=IP, port=PORT, file_name='', fps=20, window_width=WINDOW_WIDTH, window_height=WINDOW_HEIGHT, command=COMMAND):
        self.ip = ip
        self.port = port
        self.filename = file_name
        self.fps = fps
        self.window_width = window_width
        self.window_height = window_height
        self.command = command
        self.prev_time = time.time()
        self.real_fps = 0
        self.fps_media = []
        self.time_beggin = time.time()

        # Validate IP and port
        if not self.is_valid_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")
        if not (0 < port < 65536):
            raise ValueError(f"Invalid port number: {port}")

    def is_valid_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def set_up_writer(self):
        if self.filename:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            name = f"{self.filename}_{timestamp}.avi"
            return cv2.VideoWriter(name, fourcc, self.fps, (self.window_width, self.window_height), isColor=True)
        return None

    def connection(self):
        try:
            # Set up the socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Connecting to camera...")
            sock.connect((self.ip, self.port))
            logging.info("Connected to camera.")

            video_writer = self.set_up_writer()

            # Start thread for reading frames
            stop_event = threading.Event()
            frame_queue = queue.Queue(maxsize=10)  # Queue for frame sharing
            thread = threading.Thread(target=self.stream_video, args=(sock, video_writer, stop_event, frame_queue))
            thread.start()

            # OpenCV window setup
            cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Video Stream", self.window_width, self.window_height)

            while not stop_event.is_set():
                try:
                    # Get frame from the queue
                    frame = frame_queue.get(timeout=0.1)  # Wait briefly for a frame
                    if frame is not None:
                        # Perform object detection
                        frame = detect_objects(frame, net, classes)
                        cv2.imshow("Video Stream", frame)
                    else:
                        logging.warning("No frame available for display.")
                except queue.Empty:
                    continue

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logging.info(sum(self.fps_media)/len(self.fps_media))
                    stop_event.set()

            thread.join()
            cv2.destroyAllWindows()
            sock.close()
            if video_writer:
                video_writer.release()
                logging.info(f"Video saved as {self.filename}")

        except Exception as e:
            logging.error(f"Error in connection: {e}")

    def stream_video(self, sock, video_writer, stop_event, frame_queue):
        try:
            while not stop_event.is_set():
                frame = self.take_frame(sock)
                if frame is not None:
                    frame = cv2.resize(frame, (self.window_width, self.window_height))
                    frame_queue.put(frame)  # Add frame to the queue
                    if video_writer:
                        video_writer.write(frame)
                else:
                    logging.warning("Failed to retrieve frame.")
        except Exception as e:
            logging.error(f"Error in video streaming: {e}")

    def take_frame(self, sock):
        try:
            # Send the LIMA command to get a BMP image
            sock.send(self.command.encode())

            # Receive the response header
            response_header = sock.recv(62)

            # Extract DATALEN value
            header_str = response_header.decode(errors='ignore')
            data_length_start = header_str.find('DATALEN="') + len('DATALEN="')
            data_length_end = header_str.find('"', data_length_start)
            data_length = int(header_str[data_length_start:data_length_end])

            # Receive the image data
            image_data = bytearray(data_length)
            view = memoryview(image_data)

            while data_length > 0:
                n_bytes = sock.recv_into(view, min(4096, data_length))
                view = view[n_bytes:]
                data_length -= n_bytes

            # Convert image data to OpenCV format
            image_io = io.BytesIO(image_data)
            pil_image = Image.open(image_io)
            frame = np.array(pil_image)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            self.current_time = time.time()
            self.real_fps = 1 / (self.current_time - self.prev_time)
            self.fps_media.append(self.real_fps)
            self.prev_time = self.current_time
            
            cv2.putText(frame, f"Relative time: {(self.real_fps):.5f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            return frame
        except Exception as e:
            logging.error(f"Error in frame retrieval: {e}")
            return None

# Example usage
if __name__ == "__main__":
    camera = SmartCamera(file_name="")
    camera.connection()
>>>>>>> 19fc62c (qq)
