# Utilisation de la caméra PI Module 2

## Prendre une photo

```sh
libcamera-jpeg -o image.jpg
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