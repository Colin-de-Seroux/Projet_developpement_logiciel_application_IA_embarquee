# Hailo

@Authors [Colin de Seroux](https://colindeseroux.fr)

- https://github.com/Colin-de-Seroux (Perso)
- https://github.com/colindeseroux (Entreprise)
- https://colindeseroux.fr

Contactez-moi à contact@colindeseroux.fr

---

Tout au long de l'installation allez chercher les fichiers manquants sur les git. Si vous avez des erreurs par la suite pensez à prendre une ancienne version. J'ai bien l'impression qu'il n'y a aucun tests de non-régression entre les versions ni qu'elles sont vérifiées avant d'être push.

Vous avez besoin au minimum de 25G sur votre disque (ou plus en fonction de votre jeu de données de calibration) et de 16G de RAM pour faire fonctionner leur code.

## <span style="color:lightblue">Sur la Raspberry Pi 5</span>

### <span style="color:lightgreen">Initialisation</span>

```sh
sudo apt update
```

```sh
sudo apt upgrade
```

### <span style="color:lightgreen">Installation</span>

```sh
sudo apt install hailo-all
```

```sh
sudo reboot
```

### <span style="color:lightgreen">Test</span>

```sh
hailortcli fw-control identify
```

## <span style="color:lightblue">Conversion des modèles en .hef sur votre PC</span>

Se rendre dans votre wsl2.

```sh
sudo apt update
```

### <span style="color:lightgreen">Installation d'un environnement Python</span>

#### <span style="color:lightpink">venv</span>

```sh
virtualenv hailo
```

```sh
. hailo/bin/activate
```

#### <span style="color:lightpink">conda</span>

Téléchargement de miniconda.

```sh
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

Ajout des droits.

```sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
```

Installation de miniconda.

```sh
./Miniconda3-latest-Linux-x86_64.sh
```

Éteignez/Relancez wsl.

Installation de notre environnement.

```sh
conda create -n hailo python=3.9
```

Lancement de notre environnement qui devra être fait à chaque fois que vous lancez wsl.

```sh
conda activate hailo
```

### <span style="color:lightgreen">Installation de Graphviz</span>

```sh
sudo apt install graphviz graphviz-dev
```

```sh
pip install pygraphviz
```

### <span style="color:lightgreen">Installation de Hailo DFC</span>

Téléchargez la bonne version sur leur [site](https://hailo.ai/developer-zone/software-downloads/).

```sh
pip install hailo_dataflow_compiler-3.30.0-py3-none-linux_x86_64.whl
```

```sh
pip install hailo_model_zoo-2.12.0-py3-none-any.whl
```

```sh
sudo apt install python3-tk
```

```sh
sudo apt install python3-dev
```

```sh
sudo apt update
```

### <span style="color:lightgreen">Utilisation</span>

#### <span style="color:lightpink">Vérification</span>

```sh
hailomz -h
```

S'il y a une erreur, copiez manuellement les fichiers venant du [Git](https://github.com/hailo-ai/hailo_model_zoo/tree/master/hailo_model_zoo/cfg/cascades).

S'il y en a avec **_hailo_platform_**, [priez](https://hailo.ai/developer-zone/documentation/hailort-v4-20-0/?sp_referrer=drivers/pcie_linux.html) (il y a de grandes chances que vous ayez des problèmes avec votre kernel lors de l'installation des drivers si vous êtes sur wsl2, pensez à prendre une ancienne version mais les derniers modèles ne seront pas disponibles).

#### <span style="color:lightpink">Si besoin d'aides</span>

```sh
hailo tutorial
```

#### <span style="color:lightpink">Installation de jeux de données de vérification (optionnel, uniquement si vous utilisez le jeu de donné coco2017)</span>

```sh
cd ~/miniconda3/envs/hailo/lib/python3.9/site-packages
```

```sh
python hailo_model_zoo/datasets/create_coco_tfrecord.py val2017
```

```sh
python hailo_model_zoo/datasets/create_coco_tfrecord.py calib2017
```

Pour plus d'informations se référer à [docs/data](https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/DATA.rst).

#### <span style="color:orange">Actuellement avec les versions que j'utilise les commandes d'optimisation .har ainsi que la quantification 16bits ne fonctionne pas sous wsl2.</span>

#### <span style="color:lightpink">Parse</span>

```sh
hailomz parse --hw-arch hailo8l --ckpt ./yolov8n.onnx yolov8n
```

#### <span style="color:lightpink">Optimize</span>

```sh
hailomz optimize --hw-arch hailo8l --har ./yolov8n.har yolov8n
```

S'il manque le fichier comme moi.

```sh
cd ~/miniconda3/envs/hailo/lib/python3.9/site-packages/hailo_model_zoo/cfg/alls
```

```sh
mkdir generic
```

Copiez le contenu du fichier sur [alls/generic](https://github.com/hailo-ai/hailo_model_zoo/tree/master/hailo_model_zoo/cfg/alls/generic).

```sh
nano yolov8.alls
```

Changer le chemin pour avoir du absolue.

Renommez les dossiers des jeux de données si besoin.

Puis relancez.

```sh
hailomz optimize --hw-arch hailo8l --har ./yolov8n.har yolov8n
```

#### <span style="color:lightpink">Compile</span>

```sh
hailomz compile yolov8n --hw-arch hailo8l --har ./yolov8n.har
```

#### <span style="color:lightpink">Exemple concret sans faire d'optimisation personnalisé en partant de notre fichier .onnx</span>

```sh
hailomz compile yolov8n --ckpt yolov8n_trained.onnx --hw-arch hailo8l --calib-path train/images --classes 7 --performance
```

## <span style="color:lightblue">Sources</span>

- [Le code pour lancer sur une image](https://github.com/hailo-ai/Hailo-Application-Code-Examples/tree/main/runtime/python/object_detection)
- [Le code pour lancer sur une vidéo](https://github.com/hailo-ai/hailo-rpi5-examples)
- [Pour optimiser en 16bits](https://github.com/hailo-ai/Hailo-Application-Code-Examples/blob/main/compilation/16bit_optimization/model-optimization-using-16bit.ipynb)
