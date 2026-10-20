import sys
import os


from src.video_utils import VideoCrop

VIDEO_NAME= "C:\\Users\\hugo.gomes\\Desktop\\DAPA\\TinyML-Utilities\\inflamabilidade_300s_13_10_2025_09_59_50 (online-video-cutter.com) (3).mp4"
DIR = os.path.dirname(os.path.abspath(__file__))
NEGATIVE_DATASET = "negative_dataset"
POSITIVE_DATASET = "positive_dataset"


video = VideoCrop(video_name= VIDEO_NAME, dir= DIR, negative_dataset= NEGATIVE_DATASET, positive_dataset= POSITIVE_DATASET)

video.dataset_constructer()

