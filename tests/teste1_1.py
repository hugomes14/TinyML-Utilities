import sys
import os


from src.video_utils import VideoCrop

VIDEO_NAME= "teste2.avi"
DIR = os.path.dirname(os.path.abspath(__file__))
NEGATIVE_DATASET = "negative_dataset"
POSITIVE_DATASET = "positive_dataset"


video = VideoCrop(video_name= VIDEO_NAME, dir= DIR, negative_dataset= NEGATIVE_DATASET, positive_dataset= POSITIVE_DATASET)

video.dataset_constructer()

