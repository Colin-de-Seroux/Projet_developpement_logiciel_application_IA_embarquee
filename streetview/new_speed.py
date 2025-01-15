import requests
import json

# Function to get the data from Overpass API
def get_speed(lat, lon, range=50):
    url = "https://overpass-api.de/api/interpreter"
    # area[name="France"]->.searchArea;
    query = f"""
                [out:json][timeout:25];

                // Coordonnées GPS (remplacez les valeurs de latitude et longitude)
                node(around:{range}, {lat}, {lon}); // Trouve les nœuds autour du point donné
                way(bn)["maxspeed"];   // Récupère les routes connectées à ces nœuds avec une maxspeed

                // Trie par distance et limite à 1 résultat
                out body center 1;

            """
    
    try:
        print("Sending request to Overpass API...")
        response = requests.post(url, data={'data': query})
        response.raise_for_status()  # Raise an error if the request failed
        data = response.json()
        speed = int(data['elements'][0]['tags']['maxspeed'])
        print("Data fetched successfully.")
        return speed
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# when this script is called in command line, get the two or three entry paramters and call the function

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        data = get_speed(lat, lon)
        if data:
            print(json.dumps(data, indent=2))
    elif len(sys.argv) == 4:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        range = float(sys.argv[3])
        data = get_speed(lat, lon, range)
        if data:
            print(json.dumps(data, indent=2))
    else:
        print("Usage: python speed.py <latitude> <longitude>")
        sys.exit(1)