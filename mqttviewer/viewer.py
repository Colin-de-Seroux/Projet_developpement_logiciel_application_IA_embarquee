import paho.mqtt.client as mqtt
import base64
import cv2
import numpy as np
import json

# Configuration MQTT
BROKER_ADDRESS = "192.168.137.58"
BROKER_PORT = 1883
MQTT_TOPIC = "inference/images"

# Callback lors de la connexion au broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(MQTT_TOPIC)
    else:
        print("Échec de la connexion, code de retour:", rc)

# Callback lors de la réception d'un message
def on_message(client, userdata, msg):
    print("Message reçu sur le topic", msg.topic)
    try:
        # Décoder le message reçu (base64 -> image)
        image_data = base64.b64decode(json.loads(msg.payload)["image"])
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Afficher l'image
        if image is not None:
            cv2.imshow("Flux d'images MQTT", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                client.disconnect()
                cv2.destroyAllWindows()
    except Exception as e:
        print("Erreur lors du traitement de l'image:", e)

# Initialisation du client MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    # Connexion au broker MQTT
    client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

    # Boucle principale du client MQTT
    client.loop_forever()
except KeyboardInterrupt:
    print("Interruption par l'utilisateur")
    client.disconnect()
    cv2.destroyAllWindows()
except Exception as e:
    print("Erreur:", e)
