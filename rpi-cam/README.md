# Utilisation de la caméra PI Module 2

## <span style="color:lightblue">Activer l'I2C et le port série pour accéder à la caméra et au module GPS</span>
Brancher la caméra sur le port CAMERA de la raspberry
Brancher le module GPS sur le port UART du shield

```sh
sudo raspi-config
```

Activer "Interface Options -> I2C" et "Interface Options -> I2C" puis redémarrer

```sh
sudo reboot
```

## <span style="color:lightblue">Voir si la caméra est connectée</span>

```sh
libcamera-hello --list-cameras
```

## <span style="color:lightblue">Prendre une photo</span>

```sh
libcamera-jpeg -o image.jpg
```

## <span style="color:lightblue">Pour faire un direct</span>

Sur la raspberry pi :

```sh
libcamera-vid -t 0 --inline --listen --nopreview -o tcp://0.0.0.0:8080
```

### <span style="color:lightgreen">Soit sur la raspberry</span>

```sh
ffmpeg -i tcp://0.0.0.0:8080 -c:v libx264 -f hls -hls_time 2 -hls_list_size 10 -hls_segment_filename "/home/pi/nginx/rpi-cam/live/segment%03d.ts" /home/pi/nginx/rpi-cam/live/playlist.m3u8
```

L'affichage se fait sur _[raspberrypi.colindeseroux.fr:543](https://raspberrypi.colindeseroux.fr:543)_.

### <span style="color:lightgreen">Soit sur votre machine</span>

```sh
ffplay tcp://raspberrypi.colindeseroux.fr:544
```

## <span style="color:lightblue">Prendre une vidéo</span>

```sh
libcamera-vid -t 10000 -o video.h264 --rotation 180
```

### <span style="color:lightgreen">Sur votre pc</span>

```sh
scp pi@192.168.30.91:/home/pi/rpi-cam/video.h264 .
```

#### <span style="color:lightpink">Pour ubuntu</span>

```sh
sudo apt install ffmpeg
```

```sh
ffmpeg -i video.h264 -c:v copy video.mp4 -y | mpv video.mp4
```

## <span style="color:lightblue">Installation des dépendences</span>

MQTT :

```sh
sudo apt-get update && sudo apt-get upgrade
sudo apt install -y mosquitto mosquitto-clients
```

Dépendences python

```sh
pip install groveGPS
pip install paho-mqtt
pip install osmnx
```
