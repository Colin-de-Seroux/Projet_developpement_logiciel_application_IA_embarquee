from collections import defaultdict
import json
import matplotlib.pyplot as plt
import numpy as np
import os
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


def extract_predictions_from_file(coco, predictions_file: str) -> tuple:
    """
    Extrait les prédictions d'un fichier de prédictions.

    :param coco: L'objet COCO
    :param predictions_file: Le chemin du fichier de prédictions

    :return: Un tuple contenant les prédictions et les scores
    """

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


def extract_predictions_from_folder(annotations_file: str, predictions_folder: str) -> tuple:
    """
    Extrait les prédictions d'un dossier de prédictions.
    
    :param annotations_file: Le chemin du fichier d'annotations COCO
    :param predictions_folder: Le chemin du dossier de prédictions
    
    :return: Un tuple contenant les prédictions et les scores
    """
    
    coco = COCO(annotations_file)
    
    y_pred = []
    y_scores = []
    
    for prediction_file in os.listdir(predictions_folder):
        prediction_file = os.path.join(predictions_folder, prediction_file)
        pred, scores = extract_predictions_from_file(coco, prediction_file)
        y_pred.append(pred)
        y_scores.append(scores)        
    
    return y_pred, y_scores


def get_coco_predictions(coco_annotations, predictions_folder: str) -> list:
    """
    Récupère les annotations et les prédictions d'un dossier de prédictions.
    
    :param coco_annotations: L'objet COCO des annotations
    :param predictions_folder: Le chemin du dossier de prédictions
    
    :return: La liste des objets COCO des prédictions
    """
    
    coco_predictions = []
    
    for prediction_file in os.listdir(predictions_folder):
        prediction_file = os.path.join(predictions_folder, prediction_file)
        coco_pred = coco_annotations.loadRes(prediction_file)
        coco_predictions.append(coco_pred)
    
    return coco_predictions


def evaluate_metrics(coco_eval: COCOeval) -> tuple:
    """
    Évalue les métriques de détection d'objets à partir d'un objet COCOeval.
    
    :param coco_eval: L'objet COCOeval à partir duquel extraire les métriques
    
    :return: Un tuple contenant la précision, le rappel, les scores et un dictionnaire de correspondance entre les seuils IoU et leur index
    """
     
    iou_lookup = {float(format(val, ".2f")): index for index, val in enumerate(coco_eval.params.iouThrs)} 
    
    precision = coco_eval.eval["precision"]
    recall = coco_eval.eval["recall"]
    scores = coco_eval.eval["scores"]
    
    precision = np.maximum(precision, 0)
    recall = np.maximum(recall, 0)
    scores = np.nan_to_num(scores, nan=0.0, neginf=0.0, posinf=1.0)

    return precision, recall, scores, iou_lookup


def extract_metrics(precision, recall) -> dict:
    """
    Extrait les métriques de détection d'objets.
    
    :param precision: Tableau des précisions
    :param recall: Tableau des rappels
    
    :return: Un dictionnaire contenant les métriques
    """
    
    mAP_50_95 = np.mean(precision[:, :, :, 0, -1])
    precision_global = np.mean(precision[:, :, :, 0, -1])
    recall_global = np.mean(recall[:, :, 0, -1])
    f1_global = 2 * precision_global * recall_global / (precision_global + recall_global + 1e-8)
    
    metrics = {
        "mAP_50_95": mAP_50_95,
        "precision_50_95": precision_global,
        "recall_50_95": recall_global,
        "f1_score_50_95": f1_global
    }
    
    return metrics
    

def display_metrics(precision, recall, iou_lookup, class_name) -> None:
    """
    Affiche les métriques de détection d'objets.
    
    :param precision: Tableau des précisions
    :param recall: Tableau des rappels
    :param iou_lookup: Un dictionnaire de correspondance entre les seuils IoU et leur index
    :param class_name: Le nom de la classe
    
    :return: None
    """
    
    if class_name:
        print("\n|-------------------------------------|")
        print(f"| Class Name : {class_name}")
    
    print("|-------------------------------------|")
    print("| IoU | Precision | Recall | F1-Score |")
    print("|-----|-----------|--------|----------|")

    for iou, idx in iou_lookup.items():
        prec = precision[idx, :, :, 0, -1].mean()
        rec = recall[idx, :, 0, -1].mean()
        
        f1_score = 2 * prec * rec / (prec + rec + 1e-8)

        print("| {:.2f} |     {:.2f}  |   {:.2f} |   {:.2f}   |".format(
            iou, prec, rec, f1_score
        ))
    
    mAP_50_95 = np.mean(precision[:, :, :, 0, -1])
    precision_global = np.mean(precision[:, :, :, 0, -1])
    recall_global = np.mean(recall[:, :, 0, -1])
    f1_global = 2 * precision_global * recall_global / (precision_global + recall_global + 1e-8)

    print("|-------------------------------------|")
    print(f"| mAP@[.50:.95]: {mAP_50_95:.2f}")
    print(f"| Recall@[.50:.95]: {recall_global:.2f}")
    print(f"| F1-Score@[.50:.95]: {f1_global:.2f}")
    print("|-------------------------------------|")


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
    

def extract_inference_time(predictions_folder: str) -> tuple:
    """
    Extrait les temps d'inférence d'un dossier de temps d'inférence.
    
    :param predictions_folder: Le chemin du dossier des prédictions
    
    :return: La liste des fichiers de prédictions, la liste des temps d'inférence et le temps d'inférence moyen
    """
    
    prediction_files = [prediction_file for prediction_file in os.listdir(predictions_folder)]
    
    inference_times = []

    for prediction_file in prediction_files:
        predictions = json.load(open(os.path.join(predictions_folder, prediction_file)))
    
        current_inference_times = []
    
        for prediction in predictions:
            current_inference_times.append(prediction["inference_time"])
    
        inference_times.append(np.mean(current_inference_times))

    average_inference_time = np.mean(inference_times)

    prediction_files = [prediction_file.replace("predictions_", '').replace('_', ' ').replace(".json", '').replace('.', ' ') for prediction_file in prediction_files]

    return prediction_files, inference_times, average_inference_time
    
    
def plot_inference_time(prediction_files, inference_times, average_inference_time, goal, filename) -> None:
    """
    Affiche le temps d'inférence.
    
    :param prediction_files: Liste des fichiers de prédictions
    :param inference_times: Liste des temps d'inférence
    :param average_inference_time: Temps d'inférence moyen
    :param goal: But de temps d'inférence
    :param filename: Nom du fichier
    
    :return: None
    """
    
    plt.figure(figsize=(8, 6))
    plt.bar(prediction_files, inference_times, color="skyblue")
    plt.axhline(y=average_inference_time, color="red", linestyle="--", label=f"Moyenne: {average_inference_time:.2f}ms")
    plt.axhline(y=goal, color="green", linestyle="-.", label=f"But: {goal}ms")
    plt.xlabel("Fichiers")
    plt.ylabel("Temps d'inférence (ms)")
    plt.xticks(rotation=90)
    plt.title("Comparaison du temps d'inférence moyen pour chaque modèle")
    plt.grid(True)
    plt.legend()
    
    plt.savefig(f"../results/benchmarking/inference_time_{filename}.png", bbox_inches="tight")
    
    plt.show()


def plot_inference_time_mAP_50_95(prediction_files, inference_times, average_inference_time, metrics, goal, dataset_name, filename) -> None:
    """
    Affiche le temps d'inférence et la mAP.
    
    :param prediction_files: Liste des fichiers de prédictions
    :param inference_times: Liste des temps d'inférence
    :param average_inference_time: Temps d'inférence moyen
    :param metrics: Liste des métriques
    :param goal: But de temps d'inférence
    :param dataset_name: Nom du dataset
    :param filename: Nom du fichier
    
    :return: None
    """

    for prediction_file, inference_time, metric in zip(prediction_files, inference_times, metrics):
        plt.scatter(inference_time, metric["mAP_50_95"], label=prediction_file)

    plt.axvline(x=average_inference_time, color="red", linestyle="--", label=f"Moyenne: {average_inference_time:.2f}ms")
    plt.axvline(x=goal, color="green", linestyle="-.", label=f"But: {goal}ms")
    plt.xlabel("Temps (ms/img)")
    plt.ylabel(f"{dataset_name} {r'mAP$^{50-95}$'}")
    plt.title("Comparaison des temps d'inférence")
    plt.grid(True)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.5), ncol=2)
    
    plt.savefig(f"../results/benchmarking/inference_time_mAP_50_95_{filename}.png", bbox_inches="tight")
    
    plt.show()