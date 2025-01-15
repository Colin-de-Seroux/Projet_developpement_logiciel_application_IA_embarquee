import time
import io
import base64
import serial
from math import radians, cos, sin, sqrt, atan2
from picamera import PiCamera
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration MQTT
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic_images = "inference/images"
mqtt_topic_results = "inference/results"
gps_buffer = {}  # Buffer pour stocker les données GPS temporairement

# Configuration caméra
delay = 5  # Intervalle entre chaque capture (en secondes)
image_width = 640

# MQTT Setup
client = mqtt.Client()

# Configuration position
last_longitude = None
last_latitude = None
last_timestamp = None
default_gps_port = "/dev/serial0"
gps_baudrate = 9600


def connect_mqtt():
    """Connecte le client MQTT au broker."""
    try:
        client.connect(mqtt_broker, mqtt_port, 60)
        print("Connecté au broker MQTT.")
    except Exception as e:
        print(f"Erreur de connexion MQTT : {e}")

def setup_camera():
    """Initialise la caméra."""
    camera = PiCamera()
    camera.resolution = (image_width, image_width)
    return camera

def on_message(client, userdata, msg):
    """Callback pour recevoir les résultats d'inférence."""
    global gps_buffer
    try:
        # Charger les résultats en tant que dictionnaire
        inference_result = eval(msg.payload.decode())
        image_id = inference_result["image_id"]

        # Associer les données GPS correspondantes
        if image_id in gps_buffer:
            gps_data = gps_buffer.pop(image_id)
            combined_data = {
                "image_id": image_id,
                "gps_data": gps_data,
                "inference_result": inference_result
            }
            print(f"Données combinées : {combined_data}")
        else:
            print(f"Résultat reçu mais aucune donnée GPS trouvée pour image_id={image_id}")
    except Exception as e:
        print(f"Erreur lors de la réception des résultats : {e}")

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points GPS en utilisant la formule de Haversine.
    Les coordonnées sont en degrés décimaux, la distance est en kilomètres.
    """
    R = 6371  # Rayon moyen de la Terre en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def calculate_speed(lat1, lon1, time1, lat2, lon2, time2):
    """
    Calcule la vitesse en km/h entre deux points GPS donnés.
    - `lat1`, `lon1` : Latitude et longitude du point 1 (en degrés décimaux)
    - `time1` : Temps UTC du point 1 (au format hhmmss.sss)
    - `lat2`, `lon2` : Latitude et longitude du point 2 (en degrés décimaux)
    - `time2` : Temps UTC du point 2 (au format hhmmss.sss)
    """
    # Calcul de la distance entre les deux points en km
    distance = haversine(lat1, lon1, lat2, lon2)

    # Calcul du temps écoulé en secondes
    time1_seconds = int(time1[:2]) * 3600 + int(time1[2:4]) * 60 + float(time1[4:])
    time2_seconds = int(time2[:2]) * 3600 + int(time2[2:4]) * 60 + float(time2[4:])
    time_diff = time2_seconds - time1_seconds

    if time_diff <= 0:  # Gestion des cas où le temps est invalide ou nul
        return 0

    # Calcul de la vitesse en km/h
    speed_kmh = (distance / time_diff) * 3600
    return speed_kmh

def get_gps_data(gps_port):
    """Lit les données GPS depuis le module."""
    global last_latitude, last_longitude, last_timestamp
    try:
        with serial.Serial(gps_port, gps_baudrate, timeout=1) as ser:
            line = ser.readline().decode('ascii', errors='ignore')
            # print(line)
            if line.startswith("$GPGGA"):
                data = line.split(',')
                print(f"Raw Data: {data}")  # Affiche tout le message analysé
                if data[6] == "1":  # Fix valide
                    latitude_value = data[2]
                    latitude_direction = data[3]
                    longitude_value = data[4]
                    longitude_direction = data[5]
                    print(f"Latitude: {latitude_value} {latitude_direction}, Longitude: {longitude_value} {longitude_direction}")
                    latitude = convert_gps_coordinate(latitude_value, latitude_direction)
                    longitude = convert_gps_coordinate(longitude_value, longitude_direction)
                    t = datetime.now().strftime("%H%M%S.%f")
                    speed = 0
                    if ((last_longitude != None) and (last_latitude != None) and (last_timestamp != None)):
                        speed = calculate_speed(last_latitude, last_longitude, last_timestamp, latitude, longitude, t)

                    last_latitude = latitude
                    last_longitude = longitude
                    last_timestamp = t

                    return speed, (latitude, longitude)
    except Exception as e:
        print(f"Erreur GPS: {e}")
    return None, (None, None)

def convert_gps_coordinate(value, direction):
    """Convertit les coordonnées GPS NMEA en degrés décimaux."""
    if not value or not direction:
        print("Invalid value or direction")  # Log si les valeurs sont absentes
        return None

    try:
        # Séparer degrés et minutes
        if len(value.split('.')[0]) > 4:
            degrees = float(value[:3])  # Pour longitude (3 chiffres pour les degrés)
            minutes = float(value[3:])
        else:
            degrees = float(value[:2])  # Pour latitude (2 chiffres pour les degrés)
            minutes = float(value[2:])

        # Convertir en degrés décimaux
        decimal = degrees + (minutes / 60)
        if direction in ['S', 'W']:  # Sud ou Ouest implique une valeur négative
            decimal = -decimal

        return round(decimal, 6)

    except ValueError as e:
        print(f"Error parsing value: {value}, Error: {e}")
        return None

def main():
    connect_mqtt()
    client.subscribe(mqtt_topic_results)  # S'abonner au topic des résultats
    client.on_message = on_message  # Assigner la callback pour les résultats
    client.loop_start()  # Démarrer la boucle MQTT

    camera = setup_camera()
    print("Appareil photo initialisé. Capture et envoi en cours...")
    gps_port = default_gps_port

    try:
        while True:
            # Capture d'image en mémoire
            image_stream = io.BytesIO()
            camera.capture(image_stream, format='jpeg')
            image_stream.seek(0)

            image_base64 = base64.b64encode(image_stream.read()).decode('utf-8')

            # Générer un timestamp unique pour l'image
            timestamp = datetime.now().isoformat()

            # Capture des données GPS
            gps_data = get_gps_data(gps_port)
            gps_buffer[timestamp] = gps_data

            # Publier l'image et le timestamp
            payload = {
                "timestamp": timestamp,
                "image": image_base64
            }
            client.publish(mqtt_topic_images, str(payload), qos=1, retain=True)

            print(f"Image envoyée avec timestamp={timestamp}. Données GPS stockées.")

            # Attente avant la prochaine capture
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Arrêt du programme.")
    finally:
        camera.close()
        client.loop_stop()

if __name__ == "__main__":
    main()
