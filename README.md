# TinyML-Utilities

This is a tool to be use in a Artificial Vision project based on a tinyml module.

## arduino
 This module have the capability to compile and upload arduino skecthes without using Arduino IDE, you need to have arduino-cli installed and add it to the path in your environment variables. Also you need to install the #include Arduino_OV767X.h package (In cli: arduino-cli lib install Arduino_OV767X.h). The hardware used is the arduino nano 33 ble sense and the camera was the ov7675 camera from tinyml kit, no other hardware was tested. 

 SketchConfig enables you to setting up all the configuration that you need to prepare before the compiling and the uploading. If you do not know the port were you have connected the arduino board, you can check it using the available_ports function. Besides that, you have the compile and upload function that are self explanatory. 

 VideoCApture enables you to capture the camera's frames. You can save it in a video if you want, just give it a name. Otherwise it just plot the frames.   

## video_utils

This module have some tools to handle the video. You can just play the video. Or you can built the negative and positive datasets to feed the model that you to create. The VideoCroper tools takes each frame from the video and let the user to crop the frame where he want and to place the croped part into one of the dataset.  


alteração