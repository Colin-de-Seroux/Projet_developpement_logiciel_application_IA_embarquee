import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString
import math
import folium

class SpeedLimitFetcher:
    def __init__(self, cache_radius=1000):
        """
        Initialise le gestionnaire de récupération des vitesses avec mise en cache.

        Args:
            cache_radius (int): Rayon du cache autour de la dernière position chargée (en mètres).
        """
        self.graph = None
        self.center = None
        self.cache_radius = cache_radius
        self.cache_name = 'cache.graphml'

    def _update_cache(self, lat, lon):
        """
        Met à jour le cache si nécessaire en fonction de la nouvelle position.

        Args:
            lat (float): Latitude de la nouvelle position.
            lon (float): Longitude de la nouvelle position.
        """
        # Calculer la distance entre la nouvelle position et le centre actuel
        if self.center is None or ox.distance.great_circle(*self.center, lat, lon) > self.cache_radius:
            print(f"Mise à jour du cache pour ({lat}, {lon})")
            new_graph = ox.graph_from_point((lat, lon), dist=self.cache_radius, network_type='drive')

            if self.graph is not None:
                # Fusionner les graphes existants pour éviter de perdre des données
                self.graph = ox.project_graph(nx.compose(self.graph, new_graph))
            else:
                self.graph = new_graph

            self.center = (lat, lon)

    def get_nearest_road_speed(self, lat, lon, bearing):
        """
        Récupère la vitesse maximale autorisée sur une route proche en fonction de la position et de l'orientation.

        Args:
            lat (float): Latitude de la position.
            lon (float): Longitude de la position.
            bearing (float): Orientation en degrés (0 = nord, 90 = est, etc.).

        Returns:
            float: Vitesse maximale autorisée (en km/h) au point donné ou None si non disponible.
        """
        # Mettre à jour le cache si nécessaire
        self._update_cache(lat, lon)

        # Trouver le nœud le plus proche de la position
        nearest_node = ox.distance.nearest_nodes(self.graph, X=lon, Y=lat)

        # Parcourir les arêtes connectées au nœud pour trouver celle correspondant à l'orientation
        edges = list(self.graph.edges(nearest_node, data=True))
        best_edge = None
        smallest_angle_diff = 360

        for u, v, data in edges:
            # Obtenir la géométrie de l'arête
            if 'geometry' in data:
                line = data['geometry']
            else:
                line = LineString([
                    (self.graph.nodes[u]['x'], self.graph.nodes[u]['y']),
                    (self.graph.nodes[v]['x'], self.graph.nodes[v]['y'])
                ])

            # Calculer l'orientation de la route
            start, end = line.coords[0], line.coords[-1]
            road_bearing = math.degrees(math.atan2(end[0] - start[0], end[1] - start[1])) % 360

            # Calculer la différence d'angle
            angle_diff = abs((road_bearing - bearing + 180) % 360 - 180)

            # Trouver l'arête la plus alignée avec l'orientation
            if angle_diff < smallest_angle_diff:
                smallest_angle_diff = angle_diff
                best_edge = data

        if best_edge is not None:
            if 'geometry' in best_edge:
                line = best_edge['geometry']
                point = Point(lon, lat)
                nearest_point = line.interpolate(line.project(point))

                # Identifier la vitesse maximale applicable pour la portion contenant le point
                max_speed = best_edge.get('maxspeed')
                if max_speed:
                    if isinstance(max_speed, list) and len(max_speed) == len(line.coords) - 1:
                        # Identifier le segment correspondant au point exact
                        for i in range(len(line.coords) - 1):
                            segment = LineString([line.coords[i], line.coords[i + 1]])
                            if segment.distance(nearest_point) < 1e-6:  # Si le point est sur ce segment
                                max_speed = max_speed[i]
                                break
                    elif isinstance(max_speed, str) and 'mph' in max_speed.lower():
                        return float(max_speed.split()[0]) * 1.60934  # Conversion mph -> km/h
                    else:
                        max_speed = float(max_speed[0]) if isinstance(max_speed, list) else float(max_speed)

                    return max_speed

        return None
    
    def download_cache(self, lat, lon, radius, filename='cache.graphml'):
        """
        Télécharge le cache du graphe dans un fichier.

        Args:
            filename (str): Nom du fichier de sortie.
        """
        self.cache_radius = radius
        self._update_cache(lat, lon)
        ox.save_graphml(self.graph, filename)


def calculate_orientations(positions):
    """
    Calcule les orientations (bearings) entre les points consécutifs.

    Args:
        positions (list of tuple): Liste de positions (latitude, longitude).

    Returns:
        list: Liste des orientations en degrés.
    """
    orientations = []
    for i in range(len(positions) - 1):
        lat1, lon1 = positions[i]
        lat2, lon2 = positions[i + 1]
        delta_lon = math.radians(lon2 - lon1)
        lat1, lat2 = map(math.radians, [lat1, lat2])

        x = math.sin(delta_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
        orientations.append(bearing)

    # Ajouter une orientation fictive pour le dernier point
    orientations.append(orientations[-1])
    return orientations

def get_coordinates_with_orientation():
    """
    Charge les positions depuis un fichier et calcule les orientations.

    Returns:
        list of tuple: Liste des positions avec orientation (lat, lon, bearing).
    """
    positions = []
    with open('./positions.txt', 'r') as f:
        for line in f.read().splitlines():
            if line.strip() and line[0].isdigit():  # Ignorer les lignes vides
                lat, lon = map(float, line.split(','))
                positions.append((lat, lon))

    orientations = calculate_orientations(positions)
    return [(lat, lon, heading) for (lat, lon), heading in zip(positions, orientations)]

def generate_speed_map(output_file='map.html'):
    """
    Génère une carte HTML avec les routes colorées en fonction des vitesses.

    Args:
        output_file (str): Nom du fichier de sortie.
    """
    fetcher = SpeedLimitFetcher()
    positions = get_coordinates_with_orientation()

    # Initialiser la carte
    m = folium.Map(location=[positions[0][0], positions[0][1]], zoom_start=15)

    for i in range(len(positions) - 1):
        lat1, lon1, bearing1 = positions[i]
        lat2, lon2, _ = positions[i + 1]

        # Obtenir la vitesse pour le segment courant
        speed = fetcher.get_nearest_road_speed(lat1, lon1, bearing1)
        color = 'gray'  # Couleur par défaut si vitesse non disponible
        if speed:
            if speed <= 30:
                color = 'red'
            elif speed <= 50:
                color = 'orange'
            elif speed <= 90:
                color = 'yellow'
            else:
                color = 'green'

        # Ajouter un segment à la carte
        folium.PolyLine([(lat1, lon1), (lat2, lon2)], color=color, weight=5).add_to(m)

    # Sauvegarder la carte
    m.save(output_file)

# Générer la carte
generate_speed_map()
