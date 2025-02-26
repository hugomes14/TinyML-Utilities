import sys
import os


from src.video_utils import VideoCropYolo

VIDEO_NAME= "teste3.avi"
DIR = os.path.dirname(os.path.abspath(__file__))
DATASET = "yolo_dataset"
FILE_NUMBER = 2



video = VideoCropYolo(video_name= VIDEO_NAME, dir= DIR, dataset= DATASET, file_number= FILE_NUMBER)

video.dataset_constructer()