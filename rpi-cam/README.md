# Utilisation de la caméra PI Module 2

## Voir si la caméra est connectée

```sh
libcamera-hello --list-cameras
```

## Prendre une photo

```sh
libcamera-jpeg -o image.jpg
```

## Pour faire un direct

Sur la raspberry pi :

```sh
libcamera-vid -t 0 --inline --listen --nopreview -o tcp://0.0.0.0:8080
```

### Soit sur la raspberry

```sh
ffmpeg -i tcp://0.0.0.0:8080 -c:v libx264 -f hls -hls_time 2 -hls_list_size 10 -hls_segment_filename "/home/pi/nginx/rpi-cam/live/segment%03d.ts" /home/pi/nginx/rpi-cam/live/playlist.m3u8
```

L'affichage se fait sur _[raspberrypi.colindeseroux.fr:543](https://raspberrypi.colindeseroux.fr:543)_.

### Soit sur votre machine

```sh
ffplay tcp://raspberrypi.colindeseroux.fr:544
```

## Prendre une vidéo

```sh
libcamera-vid -t 10000 -o video.h264 --rotation 180
```

### Sur votre pc

```sh
scp pi@192.168.30.91:/home/pi/rpi-cam/video.h264 .
```

#### Pour ubuntu

```sh
sudo apt install ffmpeg
```

```sh
ffmpeg -i video.h264 -c:v copy video.mp4 -y | mpv video.mp4
```