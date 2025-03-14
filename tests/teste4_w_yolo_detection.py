from src.b6_smart_camera import SmartCamera

camera = SmartCamera(file_name="", detection= True, model_path= "/home/dapa/Documentos/TinyML-Utilities/custom_logs/train8/weights/best.pt", confiance= 0.1)
camera.connection()