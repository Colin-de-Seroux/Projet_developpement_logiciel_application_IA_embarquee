from playwright.sync_api import sync_playwright
from PIL import Image
import os
import math
import folium
import matplotlib.pyplot as plt

def calculate_orientations(coordinates):
    """
    Calcule les orientations entre des points successifs.
    
    :param coordinates: Liste de tuples (latitude, longitude)
    :return: Liste des orientations (azimuts) en degrés
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
        orientations.append(int(azimuth_degrees)*100/100)
    
    return orientations

def get_streetview_images(positions, output_folder, headless=True):
    """
    Capture des images de Street View pour une liste de positions GPS.

    :param positions: Liste des positions au format [(lat, lon, heading), ...]
    :param output_folder: Chemin du dossier où les images seront sauvegardées
    """
    # remove previous images
    for file in os.listdir(output_folder):
        if file.endswith(".png"):
            os.remove(os.path.join(output_folder, file))

    with sync_playwright() as p:
        # Spécifiez le chemin de l'exécutable Chromium si nécessaire
        browser = p.chromium.launch(executable_path="C:\\Users\\trist\\AppData\\Local\\ms-playwright\\chromium-1067\\chrome-win\\chrome.exe", headless=headless)
        page = browser.new_page()
        page.goto('https://www.google.com/maps')
        try:
            page.wait_for_selector('button[aria-label="Tout accepter"]', timeout=5000).click()
        except:
            print("Pas de bouton de consentement visible")
        
        taille = len(positions)
        fill = len(str(taille))

        for i, [lat, lon, heading] in enumerate(positions):
            # Charger l'URL Street View
            page.goto(f'https://www.google.com/maps/@{lat},{lon},3a,75y,{heading}h,90t/data=!3m6!1e1!3m4!1s6TlniPdxCV98aICBlE0l0g!2e0!7i16384!8i8192?entry=ttu')

            # Attendre que le canvas Street View soit prêt
            canvas_selector = "canvas.widget-scene-canvas[height='720'][width='1280']"
            page.wait_for_selector(canvas_selector)
            page.wait_for_timeout(2000)

            # Capturer uniquement le canvas
            canvas = page.locator(canvas_selector).first
            output_file = f"{output_folder}/{str(i).zfill(fill)}_streetview_{lat}_{lon}_{heading}.png"
            canvas.screenshot(path=output_file)
            print(f"Image {i+1}/{taille} capturée : {output_file}")

        browser.close()

def create_gif(image_folder, output_file, duration=500):
    """
    Crée un GIF à partir des images dans un dossier donné.

    :param image_folder: Chemin du dossier contenant les images.
    :param output_file: Chemin du fichier GIF de sortie.
    :param duration: Durée entre les images en millisecondes (par défaut 500ms).
    """
    # Récupérer tous les fichiers d'images dans le dossier
    images = [
        os.path.join(image_folder, f)
        for f in sorted(os.listdir(image_folder))
        if f.endswith(".png")
    ]
    
    if not images:
        raise ValueError("Aucune image trouvée dans le dossier spécifié.")

    # Charger les images
    frames = [Image.open(img) for img in images]

    # Créer le GIF
    frames[0].save(
        output_file,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=duration,
        loop=0,  # Boucle infinie
    )
    print(f"GIF créé : {output_file}")

def get_coordinates_with_orientation():
    # Charger les positions depuis un fichier texte
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

def plot_positions_on_map(positions):
    """
    Trace les positions sur une carte statique.

    :param positions: Liste des positions au format [(lat, lon, heading), ...]
    """
    # Créer une carte centrée sur la première position
    m = folium.Map(location=positions[0][:2], zoom_start=15)
    max_positions = len(positions) -1

    # Ajouter un marqueur pour chaque position
    for i, [lat, lon, heading] in enumerate(positions):
        folium.Marker(
            location=[lat, lon],
            popup=f"Orientation : {heading:.2f}°",
            icon=folium.Icon(color=["blue", "green"][i == 0 or i == max_positions], icon="info-sign"),
            rotation_angle=heading,
        ).add_to(m)
    
    # Sauvegarder la carte
    m.save("cache/positions_map.html")
    
    # plot the route on a top graph and the orientations on a bottom graph
    fig, ax = plt.subplots(3, 1, figsize=(5, 7), gridspec_kw={'height_ratios': [2, 1, 1]})
    ax[0].plot([lon for lat, lon, heading in positions], [lat for lat, lon, heading in positions])
    ax[0].set_title("Route")
    ax[0].set_xlabel("Longitude")
    ax[0].set_ylabel("Latitude")
    ax[1].plot([heading for lat, lon, heading in positions])
    ax[1].set_title("Orientations")
    ax[1].set_xlabel("Index")
    ax[1].set_ylabel("Heading")
    derived = [positions[i+1][2] - positions[i][2] for i in range(len(positions) - 1)]
    ax[2].plot(range(len(derived)), derived, label="Derived heading")
    plt.tight_layout()
    plt.savefig("cache/positions_plot.png")

    # add the plot to the map in a div on the right of the page
    with open("cache/positions_map.html", "r") as f:
        data = f.read()
    
    data = data.replace("</body>", f"<div class='plot'><img src='positions_plot.png'></div></body>")
    data = data.replace("</head>", "<style>.folium-map {width:70vw;} body {display: flex;} .plot {width:30vw;} img {max-width:100%;}</style></head>")
        
    with open("cache/positions_map.html", "w") as f:
        f.write(data)

    print("Carte sauvegardée : positions_map.html")

if __name__ == "__main__":
    HEADLESS = True # Changer à True pour exécuter en mode headless
    
    positions = get_coordinates_with_orientation()
    plot_positions_on_map(positions)

    # Appeler la fonction pour capturer les images
    output_folder = "./images"
    get_streetview_images(positions, output_folder, headless=HEADLESS)

    # Créer le GIF à partir des images capturées
    create_gif(output_folder, "streetview.gif", duration=100)
