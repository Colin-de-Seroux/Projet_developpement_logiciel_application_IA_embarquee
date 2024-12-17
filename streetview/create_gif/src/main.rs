use std::env;
use std::fs;
use std::path::PathBuf;
use gif::{Encoder, Frame, Repeat};
use image::{GenericImageView};
use rayon::prelude::*;

fn main() {
    let current_dir = env::current_dir().expect("Impossible de récupérer le dossier actuel");
    let default_input_folder = current_dir.join("../images");
    let default_output_path = current_dir.join("../output.gif");

    let args: Vec<String> = env::args().collect();
    let input_folder = args.get(1).map_or(default_input_folder.clone(), |s| PathBuf::from(s));
    let output_path = args.get(2).map_or(default_output_path.clone(), |s| PathBuf::from(s));

    println!("Dossier d'entrée : {:?}", input_folder);
    println!("Fichier de sortie : {:?}", output_path);

    let frame_delay = 10;

    println!("Lecture des fichiers dans le dossier...");
    let mut image_files: Vec<_> = fs::read_dir(&input_folder)
        .expect("Erreur lors de la lecture du dossier")
        .filter_map(|entry| {
            let path = entry.ok()?.path();
            if path.extension()?.to_str()?.to_lowercase() == "png" {
                Some(path)
            } else {
                None
            }
        })
        .collect();

    image_files.sort();

    if image_files.is_empty() {
        eprintln!("Aucune image PNG trouvée dans le dossier.");
        return;
    }

    println!("{} images trouvées.", image_files.len());
    let first_image = image::open(&image_files[0]).expect("Erreur lors du chargement de l'image");
    let (width, height) = first_image.dimensions();
    println!("Dimensions : {}x{}", width, height);

    let mut output_file = fs::File::create(&output_path).expect("Impossible de créer le fichier GIF");
    let mut encoder = Encoder::new(&mut output_file, width as u16, height as u16, &[]).unwrap();
    encoder.set_repeat(Repeat::Infinite).unwrap();

    println!("Traitement des images par batch...");
    let batch_size = 500;
    let total_images = image_files.len();
    for (batch_index, batch) in image_files.chunks(batch_size).enumerate() {
        println!("Batch {}/{}", batch_index + 1, (total_images + batch_size - 1) / batch_size);

        let frames: Vec<Frame> = batch
            .par_iter()
            .enumerate()
            .map(|(index, image_path)| {    
                let image = image::open(&image_path).expect("Erreur lors du chargement de l'image");
                let image = image.to_rgba8();
                let mut frame = Frame::from_rgba(width as u16, height as u16, &mut image.into_raw());
                frame.delay = frame_delay;
                frame
            })
            .collect();

        for frame in frames {
            encoder.write_frame(&frame).unwrap();
        }
    }

    println!("GIF créé avec succès : {:?}", output_path);
}
