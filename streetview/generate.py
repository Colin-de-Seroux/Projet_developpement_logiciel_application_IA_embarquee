import csv
from geopy.distance import geodesic
import math
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, Point
import numpy as np

def generate_linear_coordinates(start, end, step):
    """
    Génère des coordonnées entre deux points GPS à intervalles réguliers.
    
    :param start: Tuple de coordonnées (latitude, longitude) de départ
    :param end: Tuple de coordonnées (latitude, longitude) d'arrivée
    :param step: Distance en mètres entre chaque point généré
    :return: Liste de tuples (latitude, longitude)
    """
    points = [start]
    distance = geodesic(start, end).meters
    num_points = math.ceil(distance / step)
    
    for i in range(1, num_points + 1):
        fraction = i / num_points
        lat = start[0] + fraction * (end[0] - start[0])
        lon = start[1] + fraction * (end[1] - start[1])
        points.append((lat, lon))
    
    return points


def get_points_along_route(start_point, end_point, interval=1):
    """
    Obtenir des points tous les 'interval' mètres le long d'une route entre deux points.
    
    :param start_point: Tuple de coordonnées (latitude, longitude) du point de départ.
    :param end_point: Tuple de coordonnées (latitude, longitude) du point d'arrivée.
    :param interval: Distance en mètres entre les points générés.
    :return: Liste de tuples (latitude, longitude) des points interpolés.
    """
    # delete previous cache
    ox.settings.cache_folder = './cache'
    ox.settings.cache_name = 'cache_map'
    ox.settings.overwrite_cache = True
    center = (np.mean([start_point[0], end_point[0]]), np.mean([start_point[1], end_point[1]]))
    radius = geodesic(center, start_point).meters + 100  # Rayon de la zone de téléchargement
              
    print("Téléchargement du graphe des routes...")
    # Télécharger le graphe des routes
    G = ox.graph_from_point(center, dist=radius, network_type='drive')
    print("Graphe des routes téléchargé.")
    
    # Trouver les nœuds les plus proches des points de départ et d'arrivée
    orig_node = ox.distance.nearest_nodes(G, start_point[1], start_point[0])
    dest_node = ox.distance.nearest_nodes(G, end_point[1], end_point[0])
    
    # Calculer le chemin le plus court (en termes de longueur géométrique)
    route = nx.shortest_path(G, orig_node, dest_node, weight='length')
    
    # Extraire les géométries de la route
    path_geom = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        edge_data = min(G[u][v].values(), key=lambda x: x['length'])
        
        # Vérifier si la géométrie existe, sinon utiliser les nœuds directement
        if 'geometry' in edge_data:
            path_geom.extend(edge_data['geometry'].coords)
        else:
            # Ajouter un segment droit entre les deux nœuds
            path_geom.append((G.nodes[u]['x'], G.nodes[u]['y']))
            path_geom.append((G.nodes[v]['x'], G.nodes[v]['y']))
    
    # pour chaque point de la route, on va calculer la distance entre le point et le point suivant
    # si cette distance est supérieure à l'intervalle, on va ajouter des points intermédiaires

    points = [start_point]
    for i in range(len(path_geom) - 1):
        p1 = path_geom[i]
        p2 = path_geom[i + 1]
        line = LineString([p1, p2])
        distance = line.length
        
        if distance > interval:
            num_points = math.ceil(distance / interval)
            for j in range(1, num_points + 1):
                fraction = j / num_points
                point = line.interpolate(fraction, normalized=True)
                if (point.y, point.x) != points[-1]:
                    points.append((point.y, point.x))
        elif (p2[1], p2[0]) != points[-1]:
            points.append((p2[1], p2[0]))
    
    return points


def save_to_csv(coordinates, filename):
    """
    Sauvegarde une liste de coordonnées GPS dans un fichier CSV.
    
    :param coordinates: Liste de tuples (latitude, longitude)
    :param filename: Nom du fichier CSV
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Latitude", "Longitude"])  # En-tête
        writer.writerows(coordinates)

# Coordonnées de départ et d'arrivée (Paris, avenue des Champs-Élysées)
start_coordinates = (43.657573, 7.128430)
end_coordinates = (43.6282301,7.0357206)

start_coordinates = (43.657557, 7.128448) # aller en ardèche
end_coordinates = (44.632738, 4.253234)

# Coordoonnées de départ et d'arrivée (route random, Alpes Maritimes)
start_coordinates = (43.651981, 7.127544)
end_coordinates = (43.642865,7.1248359)

# coordonnées de départ et d'arrivée (depuis amadeux villeneuve vers air france sophia)
start_coordinates = (43.642865,7.1248359)
end_coordinates = (43.6281792,7.0356255)

# Générer les coordonnées avec un pas de 10 mètres
step_distance = 1  # mètres
#result = generate_linear_coordinates(start_coordinates, end_coordinates, step_distance)
result = get_points_along_route(start_coordinates, end_coordinates, step_distance)

print(f"Nombre de points générés : {len(result)}")


# Sauvegarder dans un fichier CSV
csv_filename = "positions.txt"
save_to_csv(result, csv_filename)

print(f"Coordonnées sauvegardées dans le fichier {csv_filename}")
