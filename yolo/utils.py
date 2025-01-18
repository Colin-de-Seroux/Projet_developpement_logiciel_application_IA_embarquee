from ultralytics import YOLO

@DeprecationWarning
def export_model(model_name: str = "yolov8n", format: str = "onnx", device : str = "cpu", image_size : int = 640) -> str:
    """
    Exportation du modèle YOLO dans un certain format.

    :param model_name : Nom du modèle à exporter.
    :param format : Format d'exportation du modèle.
    :param device : Périphérique sur lequel le modèle doit être exporté (GPU -> 0, CPU -> cpu, NVDIA Jetson -> dla:0 / dla:1).
    :param image_size : Taille de l'image d'entrée du modèle.
    """

    model = YOLO(f"./saved/{model_name}.pt")

    return model.export(format=format, device=device, imgsz=image_size)