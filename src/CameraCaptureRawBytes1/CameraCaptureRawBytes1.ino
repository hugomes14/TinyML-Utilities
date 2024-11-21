#include <Arduino_OV767X.h>

int bytesPerFrame;
byte data[320*240]; // QVGA: 320x240 X 1 byte per pixel (grayscale)

void setup() {
  Serial.begin(256000);
  while (!Serial);

  // Initialize the camera in grayscale mode
  if (!Camera.begin(QVGA, GRAYSCALE, 5)) {
    Serial.println("Failed to initialize camera!");
    while (1);
  }

  bytesPerFrame = Camera.width() * Camera.height(); // 1 byte per pixel for grayscale

  // Optionally, enable the test pattern for testing
  // Camera.testPattern();
  while (Serial.read() != 0xC0) {
    // Wait for the command to start reading
  }
}

void loop() {
  Camera.readFrame(data);

  Serial.write(data, bytesPerFrame);
  Serial.write(0xC0); // Send a command to indicate the end of the frame


  //delay(100); // Adjust delay as needed
}