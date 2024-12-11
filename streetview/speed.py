import osmnx as ox
from shapely.geometry import Point, LineString
import math

def get_nearest_road_speed(lat, lon, bearing):
    """
    Récupère la vitesse maximale autorisée sur une route proche en fonction de la position et de l'orientation.

    Args:
        lat (float): Latitude de la position.
        lon (float): Longitude de la position.
        bearing (float): Orientation en degrés (0 = nord, 90 = est, etc.).

    Returns:
        float: Vitesse maximale autorisée (en km/h) au point donné ou None si non disponible.
    """
    # Télécharger les données OSM pour la zone autour de la position
    print(f"Téléchargement des données OSM autour de la position ({lat}, {lon})")
    G = ox.graph_from_point((lat, lon), dist=1000, network_type='drive')

    # Trouver le nœud le plus proche de la position
    nearest_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    print(f"Nœud le plus proche trouvé : {nearest_node}")

    # Parcourir les arêtes connectées au nœud pour trouver celle correspondant à l'orientation
    edges = list(G.edges(nearest_node, data=True))
    print(f"Arêtes connectées au nœud : {len(edges)}")
    best_edge = None
    smallest_angle_diff = 360

    for u, v, data in edges:
        print(f"Traitement de l'arête entre les nœuds {u} et {v}")
        # Obtenir la géométrie de l'arête
        if 'geometry' in data:
            line = data['geometry']
        else:
            line = LineString([(G.nodes[u]['x'], G.nodes[u]['y']), (G.nodes[v]['x'], G.nodes[v]['y'])])

        # Calculer l'orientation de la route
        start, end = line.coords[0], line.coords[-1]
        road_bearing = math.degrees(math.atan2(end[0] - start[0], end[1] - start[1])) % 360
        print(f"Orientation de la route : {road_bearing}°")

        # Calculer la différence d'angle
        angle_diff = abs((road_bearing - bearing + 180) % 360 - 180)
        print(f"Différence d'angle : {angle_diff}°")

        # Trouver l'arête la plus alignée avec l'orientation
        if angle_diff < smallest_angle_diff:
            smallest_angle_diff = angle_diff
            best_edge = data
            print(f"Nouvelle meilleure arête trouvée avec une différence d'angle de {smallest_angle_diff}°")

    if best_edge is not None:
        # Si la géométrie est disponible, trouver la vitesse au point exact
        print(f"Meilleure arête trouvée : {best_edge}")
        if 'geometry' in best_edge:
            line = best_edge['geometry']
            point = Point(lon, lat)
            nearest_point = line.interpolate(line.project(point))
            print(f"Point le plus proche sur la ligne : {nearest_point}")

            # Identifier la vitesse maximale applicable pour la portion contenant le point
            max_speed = best_edge.get('maxspeed')
            print(f"Vitesse maximale trouvée : {max_speed}")
            if max_speed:
                if isinstance(max_speed, list):
                    # Identifier le segment correspondant au point exact
                    for i in range(len(line.coords) - 1):
                        segment = LineString([line.coords[i], line.coords[i + 1]])
                        if segment.distance(nearest_point) < 1e-6:  # Si le point est sur ce segment
                            max_speed = max_speed[i]
                            break
                if isinstance(max_speed, str) and 'mph' in max_speed.lower():
                    return float(max_speed.split()[0]) * 1.60934  # Conversion mph -> km/h
                return float(max_speed)

    print("Aucune vitesse maximale trouvée.")
    return None

# Exemple d'utilisation
latitude = 43.6074933  # Route à Biot
longitude = 7.081915
orientation = 10  # Orientation vers Polytech

speed_limit = get_nearest_road_speed(latitude, longitude, orientation)
print(f"Vitesse maximale autorisée : {speed_limit} km/h")
