
# https://developer.precisely.com/tryApiGeoStreetMajSpeedIntersection?path=-74.044812,40.61171;-74.045644,40.613625;-74.046322,40.615183&dataType=json&clientIdentifier=LearnPageTryAPI

import requests
import matplotlib.pyplot as plt

def fetch_speed(position1, position2):  # ne fonctionne pas en France
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "fr",
        "cache-control": "no-cache",
        "contenttype": "application/json",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://developer.precisely.com/apis/streets",
        "sec-ch-ua": "\"Microsoft Edge\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    }

    url = f"https://developer.precisely.com/tryApiGeoStreetMajSpeedIntersection?path={position1};{position2}&dataType=json&clientIdentifier=LearnPageTryAPI"
    print(url)

    response = requests.get(url, headers=headers)
    data = response.json()
    return data

with open("positions.txt", "r") as f:
    positions = f.read().split("\n")[1:-1]
    print(positions[0])

    for i in range(len(positions) - 1):
        position1 = positions[i]
        position2 = positions[i + 1]
        speed = fetch_speed(position1, position2)
        print(f"Speed between {position1} and {position2} : {speed}")

    plt.plot(speed, label="Speed")
    plt.legend()
    plt.show()