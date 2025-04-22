from src.b6_smart_camera import SmartCamera

camera = SmartCamera(file_name="", detection= True, model_path= "/home/dapa/Documentos/TinyML-Utilities/custom_logs/train15/weights/best.pt", confiance= 0.8)
camera.connection()