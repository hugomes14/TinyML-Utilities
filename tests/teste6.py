from src.digital_twin import DigitalTwin

digital_twin = DigitalTwin("/home/dapa/Documentos/TinyML-Utilities/custom_logs/train17/weights/best.pt", "/home/dapa/Documentos/ML_learning/runs/segment/train4/weights/best.pt")
digital_twin.run("tests/videos/digital_mp4_preto.mp4", "tests/videos/teste3.avi", output_path="output.mp4", conf_threshold=0.5, show_video=True)