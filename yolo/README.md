# YOLO

@Author Colin de Seroux

## <span style="color:lightblue">Version</span>

yolov8n / yolo11n (je suis obligé de prendre la v8n pour hailo)

## <span style="color:lightblue">Entrainement des modèles</span>

[Par ici, par ici, venez, n'ayez pas peur.](./fine-tuning.ipynb)

## <span style="color:lightblue">Exportation des modèles</span>

[Par ici, par ici, venez, n'ayez pas peur.](./export.ipynb)

## <span style="color:lightblue">Test des modèles</span>

[Par ici, par ici, venez, n'ayez pas peur.](./test.ipynb)

## <span style="color:lightblue">Résultats</span>

![Inference time](../results/benchmarking/inference_time_DATASET_4_YOLO.png)

Comme nous pouvons le voir en mode embarqué ce qui est le plus éfficace est Hailo 8L.

![Inference time mAP_50_95](../results/benchmarking/inference_time_mAP_50_95_DATASET_4_YOLO.png)

Mais il y a une perte de précision liée au fait que l'optimisation en .har n'a pas pu être faite.

## <span style="color:lightblue">Sources</span>

### <span style="color:lightgreen">Sur raspberry pi</span>

- https://docs.ultralytics.com/fr/guides/raspberry-pi/#use-ncnn-on-raspberry-pi
- https://docs.ultralytics.com/fr/guides/raspberry-pi/#use-raspberry-pi-camera

### <span style="color:lightgreen">Sur hailo</span>

- https://github.com/hailo-ai/hailo_model_zoo/blob/master/training/yolov8/README.rst

### <span style="color:lightgreen">Sur Google Coral</span>

- https://docs.ultralytics.com/fr/guides/coral-edge-tpu-on-raspberry-pi/#what-should-i-do-if-tensorflow-is-already-installed-on-my-raspberry-pi-but-i-want-to-use-tflite-runtime-instead
- https://coral.ai/docs/accelerator/get-started/#runtime-on-linux

### <span style="color:lightgreen">Sur NVIDIA Jetson</span>

- https://docs.ultralytics.com/fr/guides/nvidia-jetson/#nvidia-jetson-series-comparison
- https://www.jetson-ai-lab.com/tutorial_ultralytics.html
