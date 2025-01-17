from collections import defaultdict
import json
import matplotlib.pyplot as plt
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import seaborn as sns


def extract_annotations_from_file(annotations_file: str) -> list:
    """
    Récupère la liste des classes prédites des annotations COCO.
    Récupère les classes d'un fichier d'annotations COCO.
    
    :param annotations_file: Le chemin du fichier d'annotations COCO
    
    :return: La liste des classes prédites et la liste des classes
    """
    
    coco = COCO(annotations_file)
    categories = coco.loadCats(coco.getCatIds())
    class_names = [cat["name"] for cat in categories]
    
    img_ids = coco.getImgIds()
    y_true = []
    
    for img_id in img_ids:
        ann_ids = coco.getAnnIds(imgIds=img_id)
        anns = coco.loadAnns(ann_ids)
        y_true.append([ann["category_id"] for ann in anns])
        
    return y_true, class_names


def extract_predictions_from_file(annotations_file: str, predictions_file: str) -> tuple:
    """
    Extrait les prédictions d'un fichier de prédictions.

    :param annotations_file: Le chemin du fichier d'annotations COCO
    :param predictions_file: Le chemin du fichier de prédictions

    :return: Un tuple contenant les prédictions et les scores
    """
    
    coco = COCO(annotations_file)

    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    
    predictions_by_image = defaultdict(list)
    
    for pred in predictions:
        predictions_by_image[pred["image_id"]].append(pred)
    
    y_pred = []
    y_scores = []

    for img_id in coco.getImgIds():
        preds = predictions_by_image.get(img_id, [])
        
        if preds:
            categories = [pred["category_id"] for pred in preds]
            scores = [pred["score"] for pred in preds]
        else:
            categories = []
            scores = [1.0]
        
        y_pred.append(categories)
        y_scores.append(scores)

    return y_pred, y_scores


def prepare_confusion_matrix(y_true, y_pred, class_names) -> tuple:
    """
    Prépare y_true_flat et y_pred_flat pour une matrice de confusion.
    
    :param y_true: Liste des catégories réelles pour chaque image (par image)
    :param y_pred: Liste des catégories prédites pour chaque image (par image)
    :param class_names: Noms des classes
    
    :return: y_true_flat, y_pred_flat et all_classes
    """
    
    all_classes = list(range(len(class_names)))
    all_classes.append(-1)

    y_true_flat = []
    y_pred_flat = []
    
    for sublist1, sublist2 in zip(y_true, y_pred):
        max_length = max(len(sublist1), len(sublist2))

        extended1 = sublist1 + [-1] * (max_length - len(sublist1))
        extended2 = sublist2 + [-1] * (max_length - len(sublist2))
        
        for elem1, elem2 in zip(extended1, extended2):
            y_true_flat.append(elem1)
            y_pred_flat.append(elem2)

    return y_true_flat, y_pred_flat, all_classes


def plot_confusion_matrix(cm, fmt, class_names, title) -> None:
    """
    Affiche une matrice de confusion.
    
    :param cm: Matrice de confusion
    :param fmt: Format des nombres dans la matrice
    :param class_names: Noms des classes
    :param title: Titre de la matrice
    
    :return: None
    """
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt=fmt,
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Prédictions")
    plt.ylabel("Vérités Terrain")
    plt.title(title)
    plt.show()
