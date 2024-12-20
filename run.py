from temp_files.script.api import *
import sys
import threading


def start ():
    while True:
        print("\n\nSelect an action or press escape to quit :")
        print(" - 1 Help")
        print(" - 2 start datapack generation")
        print(" - 3 start datapack generation (debug)")

        char = lire_touche()
        if char == '\x1b' :
            print("Bye ...")
            break
        if char == '1':
            help()
        if char == '2':
            get_info()
        if char == '3':
            standard()

def help():
    print(f"\n\nGive a name to your datapack. \nThis name will be used in all of the datapack for :\n - The namesapce\n - The functions names\n - textures names\n - folders names\nIf you want that the generated datapack to work, you need to give it a unique name that no other datapack loaded might have.", end="")
    print(f"\n\n\nGive a video to convert. this video will be converted at a frame rate of 20fps using FFMPEG (This need to be install on your computer).", end="")

def standard():
    clear_directory("packs_output/TestVideo")
    global name 
    name = "TestVideo"
    global video_path
    video_path = "video.mp4"
    global datapack_version
    datapack_version = "41"
    global ressource_version
    ressource_version = "38"
    main()

def get_info ():
    print(f"\n\n ✏️  Datapack name : ", end="")
    global name 
    name = str(input())
    print(f"\n 🎞️  Video path : ", end="")
    global video_path
    video_path = str(input())
    print(f"\n 🎮  Datapack version : ", end="")
    global datapack_version
    datapack_version = str(input())
    print(f"\n 🖼️  Ressource pack version : ", end="")
    global ressource_version
    ressource_version = str(input())
    main()
    return None

def run_in_thread(target_function, *args):
    """
    Runs a given function in a separate thread.
    
    Args:
        target_function (callable): The function to execute in a thread.
        *args: Additional arguments for the function.
    """
    thread = threading.Thread(target=target_function, args=args)
    thread.start()


def get_info():
    """
    Prompts the user for datapack configuration and runs the generation process.
    """
    print("\n\n ✏️  Datapack name : ", end="")
    global name
    name = str(input())
    print("\n 🎞️  Video path : ", end="")
    global video_path
    video_path = str(input())
    print("\n 🎮  Datapack version : ", end="")
    global datapack_version
    datapack_version = str(input())
    print("\n 🖼️  Resource pack version : ", end="")
    global ressource_version
    ressource_version = str(input())
    main()



def main():
    """
    Main function to generate the datapack and resource pack. 
    This includes folder creation, metadata generation, and multimedia processing.
    """
    try:
        # Define paths
        output_path = f"packs_output/{name}/"
        tp_text_path = f"{name}_texture_pack/assets/minecraft/textures/{name}_frames/"
        tp_sound_path = f"{name}_texture_pack/assets/minecraft/sounds/{name}_video/"
        dp_path = f"{name}_data_pack/data/"
        dp_tags_path = f"minecraft/tags/function/"
        dp_func_path = f"{name}_video/function/"

        # Create necessary directories
        os.makedirs(output_path + tp_text_path, exist_ok=True)
        os.makedirs(output_path + tp_sound_path, exist_ok=True)
        os.makedirs(output_path + dp_path + dp_tags_path, exist_ok=True)
        os.makedirs(output_path + dp_path + dp_func_path, exist_ok=True)

        # Generate pack metadata
        write_file(output_path + f"{name}_texture_pack/pack.mcmeta", generate_pack_mcmeta(ressource_version, f"texture for {name}"))
        write_file(output_path + f"{name}_data_pack/pack.mcmeta", generate_pack_mcmeta(datapack_version, f"datapack for {name}"))
        write_file(output_path + dp_path + dp_tags_path + "load.json", generate_json_tag(f"{name}_video:load"))
        write_file(output_path + dp_path + dp_tags_path + "tick.json", generate_json_tag(f"{name}_video:tick"))
        write_file(output_path + dp_path + dp_func_path + "load.mcfunction", generate_load_mcfunction(name))
        write_file(output_path + dp_path + dp_func_path + "tick.mcfunction", generate_tick_mcfunction(name))
        write_file(output_path + f"{name}_texture_pack/assets/minecraft/sounds.json", generate_sound_json(name))

        # Copy static assets
        copy_folder("temp_files/assets", output_path + f"{name}_texture_pack/assets/")

        # Multithreaded processing for video and audio
        threads = [
            threading.Thread(target=extract_and_compress_images, args=(video_path, output_path + tp_text_path)),
            threading.Thread(target=extract_audio, args=(video_path, output_path + tp_sound_path + "sound.ogg")),
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Generate mcfunction for video playback
        create_mcfunction(output_path + tp_text_path, output_path + dp_path + dp_func_path + "play_vid.mcfunction", name)

        print(f"\n✅ Datapack '{name}' generation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error in datapack generation: {e}")


def write_file(filepath, content):
    """
    Writes content to a file.
    
    Args:
        filepath (str): Path to the file.
        content (str): Content to write into the file.
    """
    with open(filepath, "w") as file:
        file.write(content)


def generate_pack_mcmeta(pack_format, description):
    """
    Generates the JSON content for a pack.mcmeta file.
    """
    return f"""{{
  "pack": {{
    "pack_format": {pack_format},
    "description": "{description}"
  }}
}}"""


def generate_json_tag(value):
    """
    Generates JSON content for load or tick tags.
    """
    return f"""{{
    "values": [
        "{value}"
    ]
}}"""


def generate_load_mcfunction(name):
    """
    Generates the content for the load.mcfunction file.
    """
    return f"""stopsound @a
scoreboard objectives add {name}_play_time dummy "time"
scoreboard objectives add {name}_play dummy "play"
scoreboard players set @a {name}_play_time 0
scoreboard players set @a {name}_play 0
"""


def generate_tick_mcfunction(name):
    """
    Generates the content for the tick.mcfunction file.
    """
    return f"execute as @a if score @s {name}_play matches 1 run function {name}_video:play_vid"


def generate_sound_json(name):
    """
    Generates the JSON content for the sounds.json file.
    """
    return f"""{{
    "{name}_video.sound": {{
        "category": "master",
        "sounds": ["{name}_video/sound"]
    }}
}}"""















if __name__ == "__main__":
    start()