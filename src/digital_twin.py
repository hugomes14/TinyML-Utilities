import cv2
from ultralytics import YOLO
import numpy as np

class DigitalTwin:
    def __init__(self, model_simulation=None, model_real=None):
        self.model_simulation = YOLO(model_simulation)
        self.model_real = YOLO(model_real)

        self.class_names_simulation = self.model_simulation.names or ['caixa-de-cima', 'caixa-de-lado', 'defeito']
        self.class_names_real = self.model_real.names or ['caixa-de-cima', 'caixa-de-lado', 'defeito']
        
        self.triggered = False
        self.first_frame = True

    def get_medium_points(self, mask_points, image_shape):
        """
        Returns 4 medium points (cluster centers) inside a mask polygon.
        """
        # Create an empty mask
        mask_img = np.zeros(image_shape[:2], dtype=np.uint8)

        # Convert polygon to correct format for fillPoly
        contour = np.array(mask_points, dtype=np.int32)
        cv2.fillPoly(mask_img, [contour], 255)

        # Get non-zero (inside) points
        points = cv2.findNonZero(mask_img)
        if points is None or len(points) < 4:
            return []

        # Prepare for k-means clustering
        points = points.reshape(-1, 2).astype(np.float32)

        # KMeans to find 4 centers
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(points, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        return centers.astype(int)

    def draw_detections(self, frame, result, class_names, conf_threshold):
        if result.masks:
            arrow = []
            masks = result.masks.xy
            confs = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)

            if len(class_ids) > 1:
                self.triggered = True

            for mask, conf, cls in zip(masks, confs, class_ids):
                if conf < conf_threshold:
                    continue
                points = [np.array(mask, dtype=np.int32)]
                label = f"{class_names[cls]}: {conf:.2f}"
                cv2.polylines(frame, points, isClosed=True, color=(148, 0, 211), thickness=2)
                # Draw filled polygon (mask)
                #cv2.fillPoly(frame, points, (148, 0, 211))  # Semi-transparent green
                x, y = points[0][0]
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                medium_pts = self.get_medium_points(mask, frame.shape)
                arrow.append(medium_pts[medium_pts[: ,0 ].argsort()])

                for pt in medium_pts:
                    cv2.circle(frame, tuple(pt), 5, (255, 0, 0), -1)

            


            if len(np.unique(class_ids)) > 1:
                for i in range(0, len(arrow[0])):
                    cv2.arrowedLine(frame, tuple(arrow[0][i]), tuple(arrow[1][i]), (255, 0, 0), 2, tipLength=0.07)
                    cv2.putText(frame, f" {np.linalg.norm(arrow[1][i] - arrow[0][i]):.2f} pixeis", tuple(arrow[0][i]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


        return frame

    def run(self, video_sim_path, video_real_path, output_path=None, conf_threshold=0.5, show_video=True):
        cap_sim = cv2.VideoCapture(video_sim_path)
        cap_real = cv2.VideoCapture(video_real_path)

        if not cap_sim.isOpened() or not cap_real.isOpened():
            print("Error: Failed to open one or both video sources.")
            return

        width, height = 640, 480
        fps = int(cap_real.get(cv2.CAP_PROP_FPS)) or 20

        out = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height))

        while True:
            if self.triggered:
                ret_sim, frame_sim = cap_sim.read()
            elif self.first_frame: 
                ret_sim, frame_sim = cap_sim.read()
                frame_sim = cv2.resize(frame_sim, (width, height))
                self.first_frame = False
                

            ret_real, frame_real = cap_real.read()

            if not ret_sim and not ret_real:
                print("End of the videos.")
                break

            if not ret_sim:
                self.triggered = False


            try:
                frame_real = cv2.resize(frame_real, (width, height))
                result_real = self.model_real.predict(frame_real, conf=conf_threshold, verbose=False)[0]
                frame_real = self.draw_detections(frame_real, result_real, self.class_names_real, conf_threshold)

                if self.triggered:
                    frame_sim = cv2.resize(frame_sim, (width, height))
                    result_sim = self.model_simulation.predict(frame_sim, conf=conf_threshold, verbose=False)[0]
                    frame_sim = self.draw_detections(frame_sim, result_sim, self.class_names_simulation, conf_threshold)
            except Exception as e:
                print(f"Error during inference: {e}")
                break

            combined = np.hstack((frame_sim, frame_real))

            if show_video:
                cv2.imshow("Digital Twin - Side by Side", combined)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            if out:
                out.write(combined)

        cap_sim.release()
        cap_real.release()
        if out:
            out.release()
        cv2.destroyAllWindows()
