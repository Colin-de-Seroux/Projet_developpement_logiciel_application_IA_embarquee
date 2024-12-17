use std::{env, process::{Command, Stdio}, fs, path::Path};

fn main() {
    // Récupérer le répertoire actuel du programme
    let current_dir = env::current_dir().expect("Impossible de récupérer le répertoire actuel");

    // Dossier des images et fichier de sortie par défaut
    let input_folder = "images"; // Dossier d'entrée des images
    let output_file = "output.mp4"; // Fichier de sortie vidéo
    
    // Construire le chemin absolu pour le dossier d'images dans le répertoir parent
    let absolute_input_folder = current_dir.parent().unwrap().join(input_folder);

    // Vérifier si le dossier d'images existe
    if !absolute_input_folder.exists() {
        println!("Le dossier des images n'existe pas : {:?}", absolute_input_folder);
        return;
    }

    // Construire le modèle de nommage des fichiers d'images
    let image_pattern = format!("{}\\*streetview_*.png", absolute_input_folder.display());

    // Afficher le chemin calculé
    println!("Chemin des images : {}", image_pattern);

    // Démarrer le processus ffmpeg avec l'option -progress
    let mut process = Command::new("ffmpeg")
        .arg("-framerate")  // Nombre d'images par seconde
        .arg("5")
        .arg("-i")  // Le modèle de fichier d'entrée
        .arg(&image_pattern)
        .arg("-c:v")  // Choisir le codec vidéo
        .arg("libx264")
        .arg("-pix_fmt")  // Format de pixels
        .arg("yuv420p")
        .arg("-y")  // Remplacer le fichier de sortie sans confirmation
        .arg(output_file)  // Fichier de sortie vidéo
        .arg("-progress")  // Afficher l'avancement
        .arg("pipe:1") // Rediriger la sortie vers le pipe
        .stdout(Stdio::piped())  // Capturer la sortie
        .stderr(Stdio::piped())  // Capturer les erreurs
        .spawn()
        .expect("Erreur lors du démarrage de ffmpeg");

    // Récupérer la sortie de ffmpeg pour afficher l'état d'avancement
    if let Some(ref mut stdout) = process.stdout {
        use std::io::{self, BufRead};
        let reader = io::BufReader::new(stdout);

        // Lire et afficher l'état d'avancement en temps réel
        for line in reader.lines() {
            if let Ok(line) = line {
                println!("{}", line);  // Afficher la ligne d'avancement
            }
        }
    }

    // Attendre la fin de l'exécution du processus ffmpeg
    let status = process.wait().expect("Erreur lors de l'attente de ffmpeg");

    // Vérification du succès de l'exécution de la commande
    if status.success() {
        println!("Vidéo créée avec succès dans le fichier {}", output_file);
    } else {
        println!("Erreur lors de la création de la vidéo");
    }
}
