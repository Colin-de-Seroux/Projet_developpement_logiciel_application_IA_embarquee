import requests
import math
from PIL import Image
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import io

def fetch_id(lat, lon):
    """
    Récupère l'identifiant Google Maps de la position à partir des coordonnées GPS.
    """
    url = f'https://www.google.com/maps/photometa/si/v1?authuser=0&hl=fr&gl=fr&pb=!1m4!1smaps_sv.tactile!11m2!2m1!1b1!2m4!1m2!3d{lat}!4d{lon}!2d50!3m17!1m2!1m1!1e2!2m2!1sfr!2sfr!9m1!1e2!11m8!1m3!1e2!2b1!3e2!1m3!1e3!2b1!3e2!4m61!1e1!1e2!1e3!1e4!1e5!1e6!1e8!1e12!1e17!2m1!1e1!4m1!1i48!5m1!1e1!5m1!1e2!6m1!1e1!6m1!1e2!9m36!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e1!2b0!3e3!1m3!1e4!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e3!11m2!3m1!4b1'
    response = requests.get(url, timeout=10)  # Timeout pour éviter les blocages
    id = response.text.split('"IMAGE_ALLEYCAT|')[1].split('"')[0]
    return id

def fetch_image(lat, lon, heading, output_folder, i, fill, size, timeout=10):
    """
    Télécharge une image StreetView et l'enregistre dans le dossier de sortie.
    """
    try:
        id = fetch_id(lat, lon)
        url = f"https://streetviewpixels-pa.googleapis.com/v1/thumbnail?cb_client=maps_sv.tactile&w={size[0]}&h={size[1]}&panoid={id}&yaw={heading}"
        response = requests.get(url, timeout=timeout)  # Timeout pour chaque téléchargement

        img = Image.open(io.BytesIO(response.content))
        output_file = f"{output_folder}/{str(i).zfill(fill)}_streetview_{lat}_{lon}_{heading}.png"

        img.save(output_file)
        print(f"Image capturée : {output_file}")
    except Exception as e:
        print(f"Erreur lors de la capture de {lat}, {lon}, {heading} : {e}")

def fetch_images_parallel(positions, output_folder, max_workers=4, size=(1800, 1200)):
    """
    Télécharge les images Street View en parallèle.
    """
    # Supprimer les images existantes
    for file in os.listdir(output_folder):
        if file.endswith(".png"):
            os.remove(os.path.join(output_folder, file))

    zfill = len(str(len(positions)))
    chrono = time.time()  # Chronométrer l'exécution

    # Utilisation d'un pool de threads pour télécharger en parallèle
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_image, lat, lon, heading, output_folder, i, zfill, size)
            for i, (lat, lon, heading) in enumerate(positions)
        ]
        
        # Gestion des futures avec délai
        for future in as_completed(futures):  # Timeout global
            try:
                future.result(timeout=30)  # Récupérer les résultats ou lever une exception
            except Exception as e:
                print(f"Erreur dans une tâche : {e}")

    taille = 0
    for path, dirs, files in os.walk("./images"):
        for f in files:
            fp = os.path.join(path, f)
            taille += os.path.getsize(fp)
    
    print(f"{len(positions)} images ({taille/1e9:.1f}Go) téléchargées en {time.time() - chrono:.2f} secondes")

def calculate_orientations(coordinates):
    """
    Calcule les orientations entre des points successifs.
    """
    orientations = []
    for i in range(len(coordinates) - 1):
        lat1, lon1 = map(math.radians, coordinates[i])
        lat2, lon2 = map(math.radians, coordinates[i + 1])

        delta_lon = lon2 - lon1

        # Calcul de l'azimut
        x = math.sin(delta_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        azimuth = math.atan2(x, y)
        
        # Convertir en degrés et normaliser
        azimuth_degrees = math.degrees(azimuth)
        azimuth_degrees = (azimuth_degrees + 360) % 360  # Normaliser entre 0 et 360
        orientations.append(int(azimuth_degrees))
    
    return orientations

def get_coordinates_with_orientation():
    """
    Charge les positions GPS et ajoute les orientations calculées.
    """
    positions = []
    with open('./positions.txt', 'r') as f:
        for line in f.read().splitlines():
            if line.strip() and line[0].isdigit():  # Ignorer les lignes vides
                lat, lon = map(float, line.split(','))
                positions.append((lat, lon))
    
    # Ajouter l'orientation calculée
    orientations = calculate_orientations(positions)
    positions = [(lat, lon, heading) for (lat, lon), heading in zip(positions, orientations)]
    return positions

def create_gif(output_folder, output_file='output.gif'):
    """
    Crée un fichier GIF à partir d'une liste d'images.
    """
    images = [f"{output_folder}/{file}" for file in sorted(os.listdir(output_folder)) if file.endswith('.png')]
    print(f"Création du GIF à partir de {len(images)} images...")
    
    # Charger les images une par une et les ajouter à une liste temporaire
    taille = len(images)
    
    first_frame = Image.open(images[0])

    for i, image in enumerate(images[1:]):
        print(f"image {i+1}/{taille}")
        with Image.open(image) as img:
            first_frame.save(f"{output_folder}/temp.gif", save_all=True, append_images=[img], loop=1, duration=200)
        
    # Renommer le fichier temporaire en GIF final
    os.rename(f"{output_folder}/temp.gif", output_file)

    print(f"GIF créé : {output_file}")

if __name__ == '__main__':
    positions = get_coordinates_with_orientation()
    output_folder = 'images'
    
    # Télécharger les images en parallèle
    fetch_images_parallel(positions, output_folder, max_workers=32, size=(450, 300))
    
    # Créer un GIF à partir des images téléchargées
    #create_gif(output_folder, 'output.gif')
