import os
import subprocess
import sys
import shutil
from concurrent.futures import ThreadPoolExecutor
import glob

# A suprimer, juste pour le test :

def clear_directory(path):
    """
    Supprime tous les sous-dossiers et fichiers dans un dossier donné.
    
    Args:
        path (str): Le chemin du dossier à nettoyer.
    """
    if not os.path.exists(path):
        print(f"Le chemin '{path}' n'existe pas.")
        return
    
    # Parcourir chaque élément dans le dossier
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        
        # Vérifie si c'est un fichier ou un dossier, puis supprime
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)  # Supprime les fichiers ou liens symboliques
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)  # Supprime les dossiers récursivement

#######################################################################################################################


if sys.platform == "win32":
    import msvcrt
    def lire_touche():
        return msvcrt.getch().decode('utf-8')
else:
    import tty, termios
    def lire_touche():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def extract_and_compress_images(video_path, output_folder, fps=20, compression_level=3, num_threads=4):
    """
    Extracts and compresses images from a video using FFmpeg, with multithreaded compression.
    
    Args:
        video_path (str): Path to the source video file.
        output_folder (str): Path to the folder where images will be saved.
        fps (int): Number of frames to extract per second.
        compression_level (int): PNG compression level (0-7).
        num_threads (int): Number of threads to use for compression.
    """
    try:
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Extract frames using FFmpeg
        output_pattern = os.path.join(output_folder, "%d.png")
        ffmpeg_command = [
            "ffmpeg", "-i", video_path, "-vf", f"fps={fps}",
            "-compression_level", str(compression_level), output_pattern
        ]
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        print(f"✅ Frames extracted successfully to '{output_folder}'.")

        # Find all PNG files in the output folder
        image_files = glob.glob(os.path.join(output_folder, "*.png"))

        # Multithreaded compression using optipng
        def compress_image(file_path):
            """
            Compress a single PNG image using optipng.
            
            Args:
                file_path (str): Path to the PNG file to compress.
            """
            try:
                subprocess.run(["optipng", "-o2", file_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print(f"Compressed: {file_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error compressing {file_path}: {e}")

        # Use ThreadPoolExecutor for parallel compression
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(compress_image, image_files)

        print(f"✅ Images compressed successfully in '{output_folder}'.")

    except FileNotFoundError:
        print(f"❌ Video file '{video_path}' not found.")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg command failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during image extraction: {e}")




def create_mcfunction(frame_folder, output_file, name):
    """
    Crée un fichier .mcfunction pour afficher une vidéo sous forme d'overlay dans Minecraft.
    
    Args:
        frame_folder (str): Dossier contenant les images.
        output_file (str): Nom du fichier mcfunction à générer.
        name (str): Nom du pack étant créer
    """
    # Compte le nombre d'images dans le dossier
    if not os.path.isdir(frame_folder):
        raise FileNotFoundError(f"Le dossier '{frame_folder}' est introuvable.")
    
    image_files = [f for f in os.listdir(frame_folder) if f.endswith((".png", ".jpg", ".jpeg"))]
    n_frames = len(image_files)
    
    if n_frames == 0:
        raise ValueError(f"Aucune image trouvée dans le dossier '{frame_folder}'.")

    # Génère les lignes du fichier mcfunction
    lines = []
    
    # Ajout des commandes pour chaque image
    for i in range(n_frames):
        command = (
            f"execute if score @s {name}_play_time matches {i + 1} "
            f"run item replace entity @s armor.head with iron_helmet[equippable={{slot:\"head\",camera_overlay:\"{name}_frames/{i + 1}\"}}, custom_name='{{\"text\":\"sup\"}}', enchantments={{binding_curse:1}}]"
        )
        lines.append(command)

    # Ajout des dernières lignes
    lines.append(f"execute if score @s {name}_play_time matches {n_frames} run clear @s minecraft:iron_helmet[custom_name='{{\"text\":\"sup\"}}']")
    lines.append(f"execute if score @s {name}_play_time matches {n_frames} run scoreboard players set @s {name}_play 0")
    lines.append(f"execute if score @s {name}_play_time matches {n_frames} run scoreboard players set @s {name}_play_time 0")
    lines.append(f"scoreboard players add @s {name}_play_time 1")

    # Écrit le fichier à la racine
    with open(output_file, "w") as f:
        f.write(f"execute at @s if score @s {name}_play_time matches 1 run playsound minecraft:{name}_video.sound master @s ~ ~ ~\n")
        f.write("\n".join(lines))
    
    print(f"Fichier '{output_file}' créé avec succès, contenant {n_frames} frames.")

def extract_audio(video_path, output_path):
    """
    Extrait le son d'une vidéo et l'exporte au format .ogg.
    
    Args:
        video_path (str): Chemin vers la vidéo source.
        output_path (str): Chemin du fichier .ogg de sortie.
    """
    # Vérifie si la vidéo source existe
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"La vidéo source '{video_path}' est introuvable.")
    
    # Vérifie si le dossier de sortie existe, sinon le crée
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Commande FFmpeg pour extraire l'audio
    command = [
        "ffmpeg",
        "-i", video_path,         # Vidéo source
        "-vn",                    # Pas de vidéo (audio uniquement)
        "-acodec", "libvorbis",   # Codec audio pour le format .ogg
        output_path               # Fichier de sortie
    ]
    
    # Exécute la commande
    try:
        subprocess.run(command, check=True)
        print(f"Audio extrait avec succès : '{output_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'extraction de l'audio : {e}")

def copy_folder(source_folder, destination_folder):
    """
    Copie un dossier et tout son contenu (fichiers et sous-dossiers) vers un autre emplacement.
    
    Args:
        source_folder (str): Chemin du dossier source à copier.
        destination_folder (str): Chemin du dossier de destination.
    """
    # Vérifie si le dossier source existe
    if not os.path.exists(source_folder):
        raise FileNotFoundError(f"Le dossier source '{source_folder}' est introuvable.")
    
    # Crée le dossier de destination s'il n'existe pas
    os.makedirs(destination_folder, exist_ok=True)
    
    # Copie le contenu du dossier source vers le dossier destination
    try:
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print(f"Dossier '{source_folder}' copié avec succès vers '{destination_folder}'.")
    except Exception as e:
        print(f"Erreur lors de la copie du dossier : {e}")
