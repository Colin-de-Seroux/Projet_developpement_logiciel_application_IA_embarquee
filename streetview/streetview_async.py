import asyncio
from playwright.async_api import async_playwright
import os
import math

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

async def capture_image(page, lat, lon, heading, output_file):
    """
    Capture une image StreetView pour une position donnée.
    """
    try:
        # Charger l'URL Street View
        await page.goto(f'https://www.google.com/maps/@{lat},{lon},3a,75y,{heading}h,90t/data=!3m6!1e1!3m4!1s6TlniPdxCV98aICBlE0l0g!2e0!7i16384!8i8192?entry=ttu', timeout=60000)
        
        # Attendre que le canvas Street View soit prêt
        canvas_selector = "canvas.widget-scene-canvas[height='720'][width='1280']"
        await page.wait_for_selector(canvas_selector)
        await asyncio.sleep(3)  # Pause pour charger le canvas

        # Capturer uniquement le canvas
        canvas = page.locator(canvas_selector).first
        await canvas.screenshot(path=output_file, timeout=60000)
        print(f"Image capturée : {output_file}")
    except Exception as e:
        print(f"Erreur lors de la capture de {lat}, {lon}, {heading} : {e}")


async def task(semaphore, browser, lat, lon, heading, output_file):
    async with semaphore:  # Limiter le nombre de tâches simultanées
        page = await browser.new_page()
        try:
            await page.wait_for_selector('button[aria-label="Tout refuser"]')
            await asyncio.sleep(2)
            await page.click('button[aria-label="Tout refuser"]')
        except:
            print("Pas de bouton de consentement visible")

        try:
            await capture_image(page, lat, lon, heading, output_file)
        finally:
            await page.close()  # Fermer la page une fois la tâche terminée

async def create_page_pool(browser, pool_size):
    """
    Crée un pool de pages pour une réutilisation dans les tâches parallèles.
    """
    pages = []
    for i in range(pool_size):
        page = await browser.new_page()
        try:
            await page.goto("https://www.google.com/maps", timeout=60000)
            await page.wait_for_selector('button[aria-label="Tout refuser"]')
            await page.click('button[aria-label="Tout refuser"]')
            print(f"Page {i+1} prête")
            pages.append(page)
        except:
            print("Pas de bouton de consentement visible")
            print(f"Erreur lors de la création de la page {i+1}")
            await page.close()
    return pages

async def close_page_pool(pages):
    """
    Ferme toutes les pages du pool.
    """
    for page in pages:
        await page.close()

async def worker_task(semaphore, page_pool, lat, lon, heading, output_file):
    """
    Tâche de travail qui utilise une page du pool pour capturer une image.
    """
    async with semaphore:
        page = page_pool.pop(0)  # Récupère une page disponible
        try:
            await capture_image(page, lat, lon, heading, output_file)
        finally:
            page_pool.append(page)  # Replace la page dans le pool après utilisation

async def get_streetview_images_async(positions, output_folder, headless=True, max_concurrent_tasks=5):
    """
    Capture des images Street View pour une liste de positions GPS en parallèle,
    en utilisant un pool de pages pour réduire la latence.
    """
    # Supprimer les images existantes
    for file in os.listdir(output_folder):
        if file.endswith(".png"):
            os.remove(os.path.join(output_folder, file))

    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="C:\\Users\\trist\\AppData\\Local\\ms-playwright\\chromium-1067\\chrome-win\\chrome.exe", headless=headless)

        # Créer le pool de pages
        page_pool = await create_page_pool(browser, max_concurrent_tasks)

        tasks = []
        taille = len(positions)
        fill = len(str(taille))

        for i, (lat, lon, heading) in enumerate(positions):
            output_file = f"{output_folder}/{str(i).zfill(fill)}_streetview_{lat}_{lon}_{heading}.png"
            tasks.append(worker_task(semaphore, page_pool, lat, lon, heading, output_file))

        # Lancer les tâches et attendre leur fin
        await asyncio.gather(*tasks)

        # Nettoyer le pool de pages
        await close_page_pool(page_pool)

        await browser.close()


# Appel de la fonction asynchrone depuis un point d'entrée synchrone
def get_streetview_images(positions, output_folder, headless=True, max_concurrent_tasks=5):
    asyncio.run(get_streetview_images_async(positions, output_folder, headless, max_concurrent_tasks))

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

if __name__ == "__main__":
    positions = get_coordinates_with_orientation()
    output_folder = "images"
    get_streetview_images(positions, output_folder, headless=True, max_concurrent_tasks=30)
    
    create_gif(output_folder, "streetview.gif", duration=500)