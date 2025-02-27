import cv2
from ultralytics import YOLO

# Load YOLO model
model = YOLO("../runs/detect/train8/weights/best.pt")  # Update model path

# Open video file (or use 0 for webcam)
video_path = "teste3.avi"
cap = cv2.VideoCapture(video_path)

# Get video properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define video writer
output_path = "output.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

# Class names
class_names = model.names if model.names else ["class_0", "class_1"]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # Stop if video ends

    # Run YOLO on the frame
    results = model.predict(frame, conf=0.1, verbose=False)  # Reduce conf to detect more
    result = results[0]  # Get first result



    if result.boxes:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)



        for box, conf, cls in zip(boxes, confs, class_ids):
            x1, y1, x2, y2 = map(int, box)  # Convert to int
            label = f"{class_names[cls]}: {conf:.2f}"

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Show frame
    cv2.imshow("YOLO Video Detection", frame)

    # Write to output video
    out.write(frame)

    # Stop early
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
out.release()
cv2.destroyAllWindows()
