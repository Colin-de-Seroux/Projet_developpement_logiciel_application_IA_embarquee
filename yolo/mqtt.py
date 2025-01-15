import base64
import json
import logging
import paho.mqtt.client as mqtt
from PIL import Image
import io
from ultralytics import YOLO


class MQTTClient:
    def __init__(self, broker, port, subscrib, publish, model_name):
        self.broker = broker
        self.port = port
        self.subscrib_topic = subscrib
        self.publish_topic = publish
        self.model = YOLO(f"./saved/{model_name}")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        logging.info(f"Connected with result code {rc}")

        self.client.subscribe(self.subscrib_topic)

    def on_message(self, client, userdata, msg):
        logging.info(f"Message received: {msg.topic}")

        payload = json.loads(msg.payload)
        image_id = payload["id"]
        image_data = base64.b64decode(payload["image"])

        image = Image.open(io.BytesIO(image_data))

        self.predict(image_id, image)

    def predict(self, image_id, image):
        results = self.model.predict(image)

        inference_time = results[0].speed["inference"]
    
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    cls = box.cls.item()
                    conf = box.conf.item()
                    boxes = box.xyxy.tolist()[0]
                    prediction = {
                        "image_id": image_id,
                        "category_id": int(cls),
                        "bbox": [boxes[0], boxes[1], boxes[2] - boxes[0], boxes[3] - boxes[1]],
                        "score": conf,
                        "inference_time": inference_time
                    }

                    self.send_message(json.dumps(prediction))

    def send_message(self, message):
        self.client.publish(self.publish_topic, message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    broker = "localhost"
    port = 1883
    subscrib = "/vroumvroum/images"
    publish = "/vroumvroum/predictions"
    model_name = "yolo11n_trained.pt"

    client = MQTTClient(broker, port, subscrib, publish, model_name)
    client.connect()

    while True:
        pass